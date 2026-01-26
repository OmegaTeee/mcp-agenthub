"""
AgentHub Router - Main FastAPI Application

A centralized MCP router that provides:
- MCP server lifecycle management (install, start, stop, monitor)
- Unified MCP server access
- Prompt enhancement via Ollama
- Response caching (L1 memory, L2 semantic)
- Circuit breaker resilience
"""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from router.config import Settings, get_settings
from router.enhancement import EnhancementService
from router.resilience import CircuitBreakerError, CircuitBreakerRegistry
from router.servers import (
    ProcessManager,
    ServerConfig,
    ServerRegistry,
    ServerStatus,
    ServerTransport,
    Supervisor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global service instances (initialized in lifespan)
registry: ServerRegistry | None = None
process_manager: ProcessManager | None = None
supervisor: Supervisor | None = None
enhancement_service: EnhancementService | None = None
circuit_breakers: CircuitBreakerRegistry | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global registry, process_manager, supervisor, enhancement_service, circuit_breakers

    # Startup
    settings = get_settings()
    logger.info(f"Starting AgentHub Router on {settings.host}:{settings.port}")

    # Initialize server management
    registry = ServerRegistry(settings.mcp_servers_config)
    registry.load()

    process_manager = ProcessManager(registry)
    supervisor = Supervisor(registry, process_manager)

    # Start supervisor (will auto-start configured servers)
    await supervisor.start()

    # Initialize circuit breaker registry
    circuit_breakers = CircuitBreakerRegistry()

    # Initialize enhancement service
    enhancement_service = EnhancementService(
        rules_path=settings.enhancement_rules_config,
        cache_max_size=500,
        cache_ttl=7200.0,
    )
    await enhancement_service.initialize()

    yield

    # Shutdown
    logger.info("Shutting down AgentHub Router")

    if enhancement_service:
        await enhancement_service.close()

    if supervisor:
        await supervisor.stop()


app = FastAPI(
    title="AgentHub Router",
    description="Centralized MCP router with server management, prompt enhancement, and caching",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Endpoints
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint - returns status of all services."""
    server_summary = supervisor.get_status_summary() if supervisor else {}

    # Check Ollama status
    ollama_status = "unknown"
    if enhancement_service:
        stats = await enhancement_service.get_stats()
        ollama_status = "up" if stats.get("ollama_healthy") else "down"

    # Get cache stats
    cache_stats = {}
    if enhancement_service:
        stats = await enhancement_service.get_stats()
        cache_stats = stats.get("cache", {})

    return {
        "status": "healthy",
        "services": {
            "router": "up",
            "ollama": ollama_status,
            "cache": {
                "status": "up",
                "hit_rate": cache_stats.get("hits", 0)
                / max(1, cache_stats.get("hits", 0) + cache_stats.get("misses", 0)),
                "size": cache_stats.get("size", 0),
            },
        },
        "servers": server_summary,
    }


@app.get("/health/{server}")
async def server_health(server: str):
    """Health check for a specific MCP server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    state = registry.get_state(server)
    if not state:
        raise HTTPException(404, f"Server {server} not found")

    # Get circuit breaker stats for this server
    cb_stats = None
    if circuit_breakers:
        breaker = circuit_breakers.get(server)
        cb_stats = breaker.stats.model_dump()

    return {
        "server": server,
        "status": state.process.status.value,
        "pid": state.process.pid,
        "restart_count": state.process.restart_count,
        "last_error": state.process.last_error,
        "circuit_breaker": cb_stats,
        "config": {
            "package": state.config.package,
            "transport": state.config.transport.value,
            "auto_start": state.config.auto_start,
        },
    }


# =============================================================================
# Server Management Endpoints
# =============================================================================


@app.get("/servers")
async def list_servers():
    """List all configured MCP servers with their status."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    states = registry.list_all()
    return {
        "servers": [
            {
                "name": state.config.name,
                "package": state.config.package,
                "transport": state.config.transport.value,
                "status": state.process.status.value,
                "pid": state.process.pid,
                "auto_start": state.config.auto_start,
                "restart_count": state.process.restart_count,
                "description": state.config.description,
            }
            for state in states
        ]
    }


@app.get("/servers/{name}")
async def get_server(name: str):
    """Get detailed information about a specific server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    state = registry.get_state(name)
    if not state:
        raise HTTPException(404, f"Server {name} not found")

    return {
        "name": state.config.name,
        "config": state.config.model_dump(),
        "process": state.process.model_dump(),
    }


@app.post("/servers/{name}/start")
async def start_server(name: str):
    """Start a stopped server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name) if registry else None
    if info and info.status == ServerStatus.RUNNING:
        raise HTTPException(400, f"Server {name} is already running")

    try:
        await supervisor.start_server(name)
        # Reset circuit breaker on manual start
        if circuit_breakers:
            circuit_breakers.reset(name)
        return {"message": f"Server {name} started", "status": "running"}
    except Exception as e:
        logger.error(f"Failed to start {name}: {e}")
        raise HTTPException(500, f"Failed to start server: {e}")


@app.post("/servers/{name}/stop")
async def stop_server(name: str):
    """Stop a running server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name) if registry else None
    if not info or info.status != ServerStatus.RUNNING:
        raise HTTPException(400, f"Server {name} is not running")

    try:
        await supervisor.stop_server(name)
        return {"message": f"Server {name} stopped", "status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop {name}: {e}")
        raise HTTPException(500, f"Failed to stop server: {e}")


@app.post("/servers/{name}/restart")
async def restart_server(name: str):
    """Restart a server."""
    if not supervisor:
        raise HTTPException(503, "Supervisor not initialized")

    config = registry.get(name) if registry else None
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    try:
        await supervisor.restart_server(name)
        # Reset circuit breaker on restart
        if circuit_breakers:
            circuit_breakers.reset(name)
        return {"message": f"Server {name} restarted", "status": "running"}
    except Exception as e:
        logger.error(f"Failed to restart {name}: {e}")
        raise HTTPException(500, f"Failed to restart server: {e}")


class InstallServerRequest(BaseModel):
    """Request body for installing a new MCP server."""

    package: str
    name: str | None = None
    auto_start: bool = False
    description: str = ""


@app.post("/servers/install")
async def install_server(request: InstallServerRequest):
    """Install and configure a new MCP server."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    # Generate name from package if not provided
    name = request.name or request.package.split("/")[-1].replace("@", "").replace(
        "-mcp", ""
    )

    # Check if already exists
    if registry.get(name):
        raise HTTPException(400, f"Server {name} already exists")

    # Create config
    config = ServerConfig(
        name=name,
        package=request.package,
        transport=ServerTransport.STDIO,
        command="npx",
        args=["-y", request.package],
        auto_start=request.auto_start,
        description=request.description,
    )

    try:
        registry.add(config)
        return {
            "message": f"Server {name} installed",
            "name": name,
            "package": request.package,
        }
    except Exception as e:
        logger.error(f"Failed to install {name}: {e}")
        raise HTTPException(500, f"Failed to install server: {e}")


@app.delete("/servers/{name}")
async def remove_server(name: str):
    """Remove a server configuration."""
    if not registry:
        raise HTTPException(503, "Server registry not initialized")

    config = registry.get(name)
    if not config:
        raise HTTPException(404, f"Server {name} not found")

    info = registry.get_process_info(name)
    if info and info.status == ServerStatus.RUNNING:
        raise HTTPException(400, f"Cannot remove running server {name}, stop it first")

    try:
        registry.remove(name)
        return {"message": f"Server {name} removed"}
    except Exception as e:
        logger.error(f"Failed to remove {name}: {e}")
        raise HTTPException(500, f"Failed to remove server: {e}")


# =============================================================================
# MCP Proxy Endpoints
# =============================================================================


@app.post("/mcp/{server}/{path:path}")
async def mcp_proxy(server: str, path: str, request: Request):
    """
    Proxy JSON-RPC requests to MCP servers.

    Args:
        server: Target MCP server name (e.g., "context7")
        path: MCP endpoint path (e.g., "tools/call")
    """
    if not supervisor or not registry or not circuit_breakers:
        raise HTTPException(503, "Services not initialized")

    # Get server config
    config = registry.get(server)
    if not config:
        raise HTTPException(404, f"Server {server} not found")

    # Check circuit breaker
    breaker = circuit_breakers.get(server)
    try:
        breaker.check()
    except CircuitBreakerError as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Server {server} circuit breaker open",
                "data": {"retry_after": e.retry_after},
            },
            "id": None,
        }

    # Check server status
    info = registry.get_process_info(server)
    if not info or info.status != ServerStatus.RUNNING:
        # Auto-start if configured
        if config.auto_start:
            try:
                await supervisor.start_server(server)
            except Exception as e:
                breaker.record_failure(e)
                raise HTTPException(503, f"Failed to auto-start server: {e}")
        else:
            raise HTTPException(503, f"Server {server} is not running")

    # Get the stdio bridge
    bridge = supervisor.get_bridge(server)
    if not bridge:
        raise HTTPException(503, f"No bridge available for server {server}")

    # Parse request body
    try:
        body = await request.json()
    except Exception:
        body = {}

    # Route based on path
    try:
        method = body.get("method", path.replace("/", "."))
        params = body.get("params", {})

        response = await bridge.send(method, params)
        breaker.record_success()
        return response

    except Exception as e:
        breaker.record_failure(e)
        logger.error(f"MCP proxy error for {server}/{path}: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": body.get("id"),
        }


# =============================================================================
# Enhancement Endpoints
# =============================================================================


class EnhanceRequest(BaseModel):
    """Request body for prompt enhancement."""

    prompt: str
    bypass_cache: bool = False


@app.post("/ollama/enhance")
async def enhance_prompt(
    body: EnhanceRequest,
    x_client_name: str | None = Header(None, alias="X-Client-Name"),
):
    """
    Enhance a prompt via Ollama.

    Headers:
        X-Client-Name: Client identifier for rule selection

    Body:
        prompt: The prompt to enhance
        bypass_cache: Skip cache lookup (default: false)

    Returns:
        original: The original prompt
        enhanced: The enhanced prompt (or original if enhancement failed)
        model: The model used for enhancement
        cached: Whether the result came from cache
        error: Error message if enhancement failed
    """
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    result = await enhancement_service.enhance(
        prompt=body.prompt,
        client_name=x_client_name,
        bypass_cache=body.bypass_cache,
    )

    return {
        "original": result.original,
        "enhanced": result.enhanced,
        "model": result.model,
        "cached": result.cached,
        "was_enhanced": result.was_enhanced,
        "error": result.error,
    }


@app.get("/ollama/stats")
async def enhancement_stats():
    """Get enhancement service statistics."""
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    return await enhancement_service.get_stats()


@app.post("/ollama/reset")
async def reset_enhancement():
    """Reset enhancement service (clear cache and circuit breaker)."""
    if not enhancement_service:
        raise HTTPException(503, "Enhancement service not initialized")

    await enhancement_service.clear_cache()
    await enhancement_service.reset_circuit_breaker()

    return {"message": "Enhancement service reset"}


# =============================================================================
# Circuit Breaker Endpoints
# =============================================================================


@app.get("/circuit-breakers")
async def list_circuit_breakers():
    """Get all circuit breaker states."""
    if not circuit_breakers:
        raise HTTPException(503, "Circuit breakers not initialized")

    return circuit_breakers.get_all_stats()


@app.post("/circuit-breakers/{name}/reset")
async def reset_circuit_breaker(name: str):
    """Reset a specific circuit breaker."""
    if not circuit_breakers:
        raise HTTPException(503, "Circuit breakers not initialized")

    if circuit_breakers.reset(name):
        return {"message": f"Circuit breaker {name} reset"}
    raise HTTPException(404, f"Circuit breaker {name} not found")


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "router.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
