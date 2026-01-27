"""
Dashboard Router.

Provides endpoints for the HTMX-powered dashboard:
- Main dashboard page
- Health status partial
- Stats partial
- Activity partial
- Quick actions (clear cache, restart servers)
"""

import re
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from router.middleware import activity_log

# Templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


def create_dashboard_router(
    get_health: Callable[[], Any],
    get_stats: Callable[[], Any],
    get_servers: Callable[[], Any],
    clear_cache: Callable[[], Any],
    restart_server: Callable[[str], Any],
    start_server: Callable[[str], Any],
    stop_server: Callable[[str], Any],
    get_circuit_breakers: Callable[[], dict[str, Any]],
) -> APIRouter:
    """
    Create the dashboard router with injected dependencies.

    Args:
        get_health: Function to get overall health status
        get_stats: Function to get enhancement stats
        get_servers: Function to get server statuses
        clear_cache: Function to clear the enhancement cache
        restart_server: Function to restart a server by name
        start_server: Function to start a server by name
        stop_server: Function to stop a server by name
        get_circuit_breakers: Function to get circuit breaker states

    Returns:
        Configured APIRouter for dashboard endpoints
    """
    router = APIRouter(prefix="/dashboard", tags=["dashboard"])
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

    @router.get("", response_class=HTMLResponse)
    async def dashboard(request: Request):
        """Main dashboard page."""
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "title": "AgentHub Dashboard",
            },
        )

    @router.get("/health-partial", response_class=HTMLResponse)
    async def health_partial(request: Request):
        """HTMX partial: Service health status."""
        # Get server statuses
        servers_data = get_servers()
        servers = []

        for name, info in servers_data.get("servers", {}).items():
            status = info.get("status", "unknown")
            status_class = "healthy" if status == "running" else "down"
            servers.append(
                {
                    "name": name,
                    "status": status,
                    "status_class": status_class,
                    "pid": info.get("pid"),
                }
            )

        # Get circuit breaker states
        breakers_data = get_circuit_breakers()
        circuit_breakers = []

        for name, stats in breakers_data.items():
            circuit_breakers.append(
                {
                    "name": name,
                    "state": stats.get("state", "unknown"),
                    "failures": stats.get("failure_count", 0),
                    "last_failure": stats.get("last_failure_time"),
                }
            )

        return templates.TemplateResponse(
            "partials/health.html",
            {
                "request": request,
                "services": servers,
                "circuit_breakers": circuit_breakers,
            },
        )

    @router.get("/stats-partial", response_class=HTMLResponse)
    async def stats_partial(request: Request):
        """HTMX partial: Enhancement cache stats."""
        stats = await get_stats()
        cache_stats = stats.get("cache", {})
        circuit_breaker = stats.get("circuit_breaker", {})

        # Calculate hit rate
        hits = cache_stats.get("hits", 0)
        misses = cache_stats.get("misses", 0)
        total = hits + misses
        hit_rate = hits / total if total > 0 else 0

        return templates.TemplateResponse(
            "partials/stats.html",
            {
                "request": request,
                "cache_stats": {
                    "hits": hits,
                    "misses": misses,
                    "hit_rate": hit_rate,
                    "total_cached": cache_stats.get("size", 0),
                    "max_size": cache_stats.get("max_size", 0),
                },
                "ollama_healthy": stats.get("ollama_healthy", False),
                "circuit_breaker": circuit_breaker,
            },
        )

    @router.get("/activity-partial", response_class=HTMLResponse)
    async def activity_partial(request: Request):
        """HTMX partial: Recent request activity."""
        activity = activity_log.get_recent(limit=50)
        return templates.TemplateResponse(
            "partials/activity.html",
            {
                "request": request,
                "activity": activity,
            },
        )

    def _validate_server_name(server: str) -> tuple[bool, str | None]:
        """
        Validate server name format and existence.

        Args:
            server: Server name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check format (alphanumeric, hyphens, underscores only)
        if not re.match(r"^[a-z0-9_-]+$", server):
            return False, "Invalid server name format"

        # Check if server exists in registry
        servers_data = get_servers()
        if server not in servers_data.get("servers", {}):
            return False, f"Server '{server}' not found"

        return True, None

    @router.post("/actions/clear-cache")
    async def clear_cache_action():
        """Clear the enhancement cache."""
        await clear_cache()
        return {"status": "success", "message": "Cache cleared"}

    @router.post("/actions/restart/{server}")
    async def restart_server_action(server: str):
        """Restart an MCP server."""
        # Validate server name
        is_valid, error_msg = _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await restart_server(server)
            return {"status": "success", "message": f"{server} restarted"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.post("/actions/start/{server}")
    async def start_server_action(server: str):
        """Start an MCP server."""
        # Validate server name
        is_valid, error_msg = _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await start_server(server)
            return {"status": "success", "message": f"{server} started"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    @router.post("/actions/stop/{server}")
    async def stop_server_action(server: str):
        """Stop an MCP server."""
        # Validate server name
        is_valid, error_msg = _validate_server_name(server)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": error_msg}
            )

        try:
            await stop_server(server)
            return {"status": "success", "message": f"{server} stopped"}
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )

    return router
