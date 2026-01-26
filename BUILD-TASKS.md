# AgentHub Build Tasks

> **Purpose**: Step-by-step checklist for building AgentHub
> **Approach**: Build one module at a time, test as you go
> **Estimated Time**: Phase 2 MVP in 1-2 weeks

---

## Prerequisites

- [ ] Python 3.11+ installed
- [ ] Docker Desktop or Colima running
- [ ] Ollama running locally (`ollama serve`)
- [ ] Node.js 20+ for MCP servers
- [ ] Virtual environment created: `python -m venv .venv && source .venv/bin/activate`

---

## Phase 2: MVP Core

### Module 1: Project Setup
**Goal**: Establish project structure and dependencies

- [ ] Create `router/` directory structure:
  ```bash
  mkdir -p router/{config,secrets,routing,resilience,cache,enhancement,middleware}
  touch router/__init__.py
  touch router/main.py
  ```

- [ ] Create `pyproject.toml`:
  ```toml
  [project]
  name = "agenthub-router"
  version = "0.1.0"
  requires-python = ">=3.11"
  dependencies = [
      "fastapi>=0.109.0",
      "uvicorn[standard]>=0.27.0",
      "httpx>=0.26.0",
      "pydantic>=2.5.0",
      "pydantic-settings>=2.1.0",
      "jinja2>=3.1.0",
  ]
  ```

- [ ] Create `requirements.txt` from pyproject.toml
- [ ] Install dependencies: `pip install -e .`
- [ ] Verify: `python -c "import fastapi; print('OK')"`

---

### Module 2: Configuration
**Goal**: Load and validate configuration files

**Files to create:**
- [ ] `router/config/__init__.py`
- [ ] `router/config/settings.py` - Pydantic settings model
- [ ] `router/config/loader.py` - JSON config loader

**Tasks:**
- [ ] Define `Settings` class with all env vars (see BUILD-SPEC.md)
- [ ] Create `load_mcp_servers()` function to parse `configs/mcp-servers.json`
- [ ] Create `load_enhancement_rules()` function to parse `configs/enhancement-rules.json`
- [ ] Add validation for required fields
- [ ] Handle missing config files gracefully (fail fast with clear error)

**Test:**
```bash
python -c "from router.config import Settings; s = Settings(); print(s.port)"
```

---

### Module 3: Circuit Breaker
**Goal**: Implement resilience pattern for service failures

**Files to create:**
- [ ] `router/resilience/__init__.py`
- [ ] `router/resilience/circuit_breaker.py`

**Tasks:**
- [ ] Define `CircuitState` enum: CLOSED, OPEN, HALF_OPEN
- [ ] Create `CircuitBreaker` class with:
  - [ ] `__init__(name, failure_threshold=3, recovery_timeout=30)`
  - [ ] `record_success()` - reset failure count
  - [ ] `record_failure()` - increment failures, maybe open circuit
  - [ ] `can_execute()` - check if request allowed
  - [ ] `state` property - current state
- [ ] Create `CircuitBreakerRegistry` to manage multiple breakers
- [ ] Add timestamp tracking for HALF_OPEN transition

**Test:**
```python
# test_circuit_breaker.py
cb = CircuitBreaker("test", failure_threshold=2)
assert cb.state == CircuitState.CLOSED
cb.record_failure()
cb.record_failure()
assert cb.state == CircuitState.OPEN
```

---

### Module 4: Cache
**Goal**: Implement L1 in-memory cache with LRU eviction

**Files to create:**
- [ ] `router/cache/__init__.py`
- [ ] `router/cache/base.py` - Abstract interface
- [ ] `router/cache/memory.py` - In-memory implementation

**Tasks:**
- [ ] Define `CacheInterface` abstract class:
  - [ ] `get(key: str) -> Optional[str]`
  - [ ] `set(key: str, value: str)`
  - [ ] `clear()`
  - [ ] `stats() -> dict`
- [ ] Implement `MemoryCache` with:
  - [ ] `collections.OrderedDict` for LRU
  - [ ] `max_size` parameter
  - [ ] Hit/miss tracking
- [ ] Add `hash_prompt(prompt: str) -> str` utility (SHA256)

**Test:**
```python
cache = MemoryCache(max_size=2)
cache.set("a", "1")
cache.set("b", "2")
cache.set("c", "3")  # Should evict "a"
assert cache.get("a") is None
assert cache.get("b") == "2"
```

---

### Module 5: Ollama Client
**Goal**: HTTP client for Ollama API

**Files to create:**
- [ ] `router/enhancement/__init__.py`
- [ ] `router/enhancement/ollama.py`

**Tasks:**
- [ ] Create `OllamaClient` class:
  - [ ] `__init__(host, port)`
  - [ ] `async generate(prompt, model, system_prompt) -> str`
  - [ ] `async health() -> bool`
- [ ] Use `httpx.AsyncClient` for requests
- [ ] Handle connection errors gracefully
- [ ] Add timeout (30 seconds default)

**Test:**
```python
client = OllamaClient("localhost", 11434)
result = await client.generate("Hello", "llama3.2:3b", "Be brief")
print(result)
```

---

### Module 6: Enhancement Middleware
**Goal**: Enhance prompts based on client rules

**Files to create:**
- [ ] `router/enhancement/middleware.py`

**Tasks:**
- [ ] Create `EnhancementService` class:
  - [ ] `__init__(ollama_client, cache, rules)`
  - [ ] `async enhance(prompt, client_name) -> str`
- [ ] Implement flow:
  1. Check cache for exact match
  2. Get client-specific rules (fallback to default)
  3. Call Ollama with model + system_prompt
  4. Cache result
  5. Return enhanced prompt
- [ ] Handle Ollama failure: return original prompt
- [ ] Track stats (hits, misses, model usage)

**Test:**
```python
service = EnhancementService(ollama, cache, rules)
enhanced = await service.enhance("explain docker", "vscode")
assert len(enhanced) > len("explain docker")
```

---

### Module 7: Server Registry & Proxy
**Goal**: Route requests to MCP servers

**Files to create:**
- [ ] `router/routing/__init__.py`
- [ ] `router/routing/registry.py`
- [ ] `router/routing/proxy.py`

**Tasks:**
- [ ] Create `ServerRegistry` class:
  - [ ] Load from `mcp-servers.json`
  - [ ] `get(server_name) -> ServerConfig`
  - [ ] `list() -> List[str]`
- [ ] Create `MCPProxy` class:
  - [ ] `__init__(registry, circuit_breakers)`
  - [ ] `async forward(server, path, body) -> dict`
- [ ] Implement flow:
  1. Look up server in registry
  2. Check circuit breaker
  3. Forward request via httpx
  4. Record success/failure
  5. Return response

**Test:**
```python
proxy = MCPProxy(registry, breakers)
result = await proxy.forward("context7", "tools/call", {"method": "..."})
```

---

### Module 8: FastAPI Application
**Goal**: Wire everything together in FastAPI

**Files to create/update:**
- [ ] `router/main.py`
- [ ] `router/middleware/logging.py`

**Tasks:**
- [ ] Create FastAPI app with lifespan (startup/shutdown)
- [ ] Initialize all services on startup:
  - [ ] Settings
  - [ ] Cache
  - [ ] CircuitBreakerRegistry
  - [ ] OllamaClient
  - [ ] EnhancementService
  - [ ] ServerRegistry
  - [ ] MCPProxy
- [ ] Implement endpoints:
  - [ ] `GET /health` - all services status
  - [ ] `GET /health/{server}` - single server
  - [ ] `POST /mcp/{server}/{path:path}` - MCP proxy
  - [ ] `POST /ollama/enhance` - direct enhancement
- [ ] Add request logging middleware
- [ ] Add CORS middleware (allow localhost)

**Test:**
```bash
uvicorn router.main:app --reload --port 9090
curl http://localhost:9090/health
curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -d '{"prompt": "explain docker"}'
```

---

### Module 9: Docker Integration
**Goal**: Containerize the router

**Tasks:**
- [ ] Update `Dockerfile` to build router:
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY pyproject.toml requirements.txt ./
  RUN pip install --no-cache-dir -r requirements.txt
  COPY router/ ./router/
  COPY configs/ ./configs/
  CMD ["uvicorn", "router.main:app", "--host", "0.0.0.0", "--port", "9090"]
  ```
- [ ] Update `docker-compose.yml` to use new router
- [ ] Test: `docker compose up --build`
- [ ] Verify health: `curl http://localhost:9090/health`

---

### Module 10: Testing Suite
**Goal**: Ensure reliability with automated tests

**Files to create:**
- [ ] `tests/__init__.py`
- [ ] `tests/conftest.py` - Pytest fixtures
- [ ] `tests/test_circuit_breaker.py`
- [ ] `tests/test_cache.py`
- [ ] `tests/test_enhancement.py`
- [ ] `tests/test_routing.py`

**Tasks:**
- [ ] Write fixtures for mock Ollama, mock MCP servers
- [ ] Test circuit breaker state transitions
- [ ] Test cache hit/miss/eviction
- [ ] Test enhancement with/without cache
- [ ] Test proxy routing success/failure

**Run:**
```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

---

## Phase 2.5: Server Management

### Module 11: Server Models
**Goal**: Define data models for server configuration and status

**Files to create:**
- [ ] `router/servers/__init__.py`
- [ ] `router/servers/models.py`

**Tasks:**
- [ ] Create `ServerTransport` enum: STDIO, HTTP
- [ ] Create `ServerStatus` enum: STOPPED, STARTING, RUNNING, FAILED, STOPPING
- [ ] Create `ServerConfig` Pydantic model with fields:
  - [ ] `name`, `package`, `transport`, `command`, `args`, `env`
  - [ ] `url` (for HTTP), `auto_start`, `restart_on_failure`
  - [ ] `max_restarts`, `health_check_interval`, `description`
- [ ] Create `ProcessInfo` model: `pid`, `status`, `started_at`, `restart_count`, `last_error`

**Test:**
```python
from router.servers.models import ServerConfig, ServerTransport
config = ServerConfig(
    name="test",
    package="@test/mcp",
    transport=ServerTransport.STDIO,
    command="npx",
    args=["-y", "@test/mcp"]
)
print(config.model_dump())
```

---

### Module 12: Server Registry
**Goal**: Load, save, and manage server configurations

**Files to create:**
- [ ] `router/servers/registry.py`

**Tasks:**
- [ ] Create `ServerRegistry` class:
  - [ ] `__init__(config_path: str)`
  - [ ] `load()` - Load servers from JSON file
  - [ ] `save()` - Save servers to JSON file
  - [ ] `get(name: str) -> ServerConfig | None`
  - [ ] `list_all() -> list[tuple[ServerConfig, ProcessInfo]]`
  - [ ] `add(config: ServerConfig)`
  - [ ] `remove(name: str)`
- [ ] Track `ProcessInfo` for each server in memory
- [ ] Support both stdio and http transport configs

**Test:**
```python
registry = ServerRegistry("configs/mcp-servers.json")
registry.load()
for config, info in registry.list_all():
    print(f"{config.name}: {info.status}")
```

---

### Module 13: Process Manager
**Goal**: Spawn and manage MCP server subprocesses

**Files to create:**
- [ ] `router/servers/process.py`

**Tasks:**
- [ ] Create `ProcessManager` class:
  - [ ] `__init__(registry: ServerRegistry)`
  - [ ] `async start(name: str) -> ProcessInfo`
  - [ ] `async stop(name: str) -> None`
  - [ ] `async restart(name: str) -> ProcessInfo`
  - [ ] `is_running(name: str) -> bool`
- [ ] Use `asyncio.create_subprocess_exec` for spawning
- [ ] Set up stdin/stdout/stderr pipes
- [ ] Store subprocess references for management
- [ ] Handle graceful shutdown (SIGTERM → wait → SIGKILL)

**Test:**
```python
pm = ProcessManager(registry)
info = await pm.start("sequential-thinking")
print(f"Started with PID: {info.pid}")
await asyncio.sleep(2)
await pm.stop("sequential-thinking")
```

---

### Module 14: Stdio Bridge
**Goal**: Bridge HTTP JSON-RPC to stdio JSON-RPC

**Files to create:**
- [ ] `router/servers/bridge.py`

**Tasks:**
- [ ] Create `StdioBridge` class:
  - [ ] `__init__(process: asyncio.subprocess.Process)`
  - [ ] `async send(method: str, params: dict) -> dict`
  - [ ] `async close()`
- [ ] Implement JSON-RPC message framing (newline-delimited JSON)
- [ ] Track request IDs and match responses
- [ ] Handle concurrent requests with asyncio.Lock or queue
- [ ] Implement read loop as background task

**Test:**
```python
bridge = StdioBridge(process)
result = await bridge.send("tools/list", {})
print(f"Available tools: {result}")
```

---

### Module 15: Supervisor
**Goal**: Monitor server health and handle auto-restart

**Files to create:**
- [ ] `router/servers/supervisor.py`

**Tasks:**
- [ ] Create `Supervisor` class:
  - [ ] `__init__(registry, process_manager)`
  - [ ] `async start()` - Start supervisor background task
  - [ ] `async stop()` - Stop supervisor and all servers
  - [ ] `async start_all_auto()` - Start servers with auto_start=true
- [ ] Implement health check loop:
  - [ ] Check if process is alive (poll())
  - [ ] If dead and restart_on_failure, restart
  - [ ] Track restart_count, respect max_restarts
  - [ ] Mark as FAILED if max exceeded
- [ ] Log all state transitions

**Test:**
```python
supervisor = Supervisor(registry, pm)
await supervisor.start()
# Kill a process externally, watch it restart
await asyncio.sleep(60)
await supervisor.stop()
```

---

### Module 16: Server Management Endpoints
**Goal**: Add REST API for server management

**Files to update:**
- [ ] `router/main.py`

**Tasks:**
- [ ] Add endpoints:
  - [ ] `GET /servers` - List all servers with status
  - [ ] `GET /servers/{name}` - Get server details
  - [ ] `POST /servers/{name}/start` - Start a server
  - [ ] `POST /servers/{name}/stop` - Stop a server
  - [ ] `POST /servers/{name}/restart` - Restart a server
  - [ ] `POST /servers/install` - Install new MCP package
  - [ ] `DELETE /servers/{name}` - Remove server from config
- [ ] Initialize Supervisor in app lifespan
- [ ] Update `/health` to include server statuses
- [ ] Update MCP proxy to use StdioBridge for stdio servers

**Test:**
```bash
# List servers
curl http://localhost:9090/servers

# Start a server
curl -X POST http://localhost:9090/servers/context7/start

# Check status
curl http://localhost:9090/servers/context7

# Stop a server
curl -X POST http://localhost:9090/servers/context7/stop
```

---

### Module 17: npm/npx Installer
**Goal**: Install MCP packages via npm

**Files to create:**
- [ ] `router/servers/installer.py`

**Tasks:**
- [ ] Create `Installer` class:
  - [ ] `async install(package: str) -> bool`
  - [ ] `async is_installed(package: str) -> bool`
  - [ ] `get_npx_path() -> str`
- [ ] Run `npm install` or rely on `npx -y` for auto-install
- [ ] Handle errors (npm not found, package not found)
- [ ] Support global vs local installation

**Test:**
```python
installer = Installer()
success = await installer.install("@modelcontextprotocol/server-memory")
print(f"Installed: {success}")
```

---

## Phase 2.5 Completion Checklist

Before moving to Phase 3, verify:

- [ ] `GET /servers` returns list of configured servers
- [ ] `POST /servers/{name}/start` starts a stopped server
- [ ] `POST /servers/{name}/stop` stops a running server
- [ ] Server auto-starts when `auto_start: true`
- [ ] Server auto-restarts when crashed (if `restart_on_failure: true`)
- [ ] Server marked FAILED after `max_restarts` exceeded
- [ ] MCP proxy works with stdio servers via StdioBridge
- [ ] `POST /servers/install` installs new packages

---

## Phase 2 Completion Checklist

Before moving to Phase 3, verify:

- [ ] `uvicorn router.main:app` starts without errors
- [ ] `curl http://localhost:9090/health` returns JSON with all services
- [ ] Enhancement works: POST to `/ollama/enhance` returns improved prompt
- [ ] Proxy works: POST to `/mcp/context7/tools/call` returns response
- [ ] Circuit breaker activates: stop a service, see OPEN state
- [ ] Circuit breaker recovers: restart service, see CLOSED state
- [ ] Cache works: same prompt twice, second is faster (check logs)
- [ ] Docker works: `docker compose up` runs the full stack
- [ ] Tests pass: `pytest tests/ -v` all green

---

## Phase 3: Desktop Integration

### Module 11: Client Configurations
**Goal**: Wire desktop apps to the router

- [ ] Create Claude Desktop config guide
- [ ] Create VS Code config guide
- [ ] Create Raycast script
- [ ] Test each client individually
- [ ] Verify X-Client-Name header affects enhancement

---

### Module 12: Pipelines
**Goal**: Implement documentation pipeline

**Files to create:**
- [ ] `router/pipelines/__init__.py`
- [ ] `router/pipelines/documentation.py`

**Tasks:**
- [ ] Create `documentation_pipeline(repo_path, project_name, vault_path)`
- [ ] Chain: enhance → sequential-thinking → desktop-commander
- [ ] Add endpoint: `POST /pipelines/documentation`
- [ ] Test with a real repository

---

## Phase 4: Dashboard

### Module 13: Dashboard Backend
**Goal**: API endpoints for dashboard

**Files to create:**
- [ ] `router/dashboard/__init__.py`
- [ ] `router/dashboard/routes.py`
- [ ] `router/dashboard/stats.py`

**Tasks:**
- [ ] Create `ActivityLog` class (deque with max 50 entries)
- [ ] Create `CacheStats` class (hits, misses, model usage)
- [ ] Implement HTMX partial endpoints
- [ ] Implement action endpoints (clear cache, restart)

---

### Module 14: Dashboard Frontend
**Goal**: HTMX-powered UI

**Files to create:**
- [ ] `templates/dashboard.html`
- [ ] `templates/partials/health.html`
- [ ] `templates/partials/stats.html`
- [ ] `templates/partials/activity.html`

**Tasks:**
- [ ] Create main dashboard layout
- [ ] Add HTMX polling for live updates
- [ ] Style with minimal CSS (dark theme)
- [ ] Test in browser: `http://localhost:9090/dashboard`

---

## Build Order Summary

```
Phase 2 (MVP):
  1. Project Setup      → Foundation
  2. Configuration      → Settings + JSON loading
  3. Circuit Breaker    → Resilience pattern
  4. Cache              → Performance optimization
  5. Ollama Client      → AI integration
  6. Enhancement        → Core value proposition
  7. Registry & Proxy   → MCP routing
  8. FastAPI App        → Wire everything
  9. Docker             → Deployment
  10. Tests             → Quality assurance

Phase 2.5 (Server Management):
  11. Server Models     → Data structures
  12. Server Registry   → Config management
  13. Process Manager   → Subprocess lifecycle
  14. Stdio Bridge      → Protocol bridging
  15. Supervisor        → Health + auto-restart
  16. Management API    → REST endpoints
  17. Installer         → npm package management

Phase 3 (Integration):
  18. Client Configs    → Connect apps
  19. Pipelines         → Workflow automation

Phase 4 (Dashboard):
  20. Dashboard Backend → Stats API
  21. Dashboard Frontend→ Visual UI
```

---

## Tips for AI Agents

1. **Build module by module** - Don't try to build everything at once
2. **Test each module** - Run the test command before moving on
3. **Check imports** - Ensure `__init__.py` exports are correct
4. **Use existing configs** - `configs/` folder has working examples
5. **Reference BUILD-SPEC.md** - For detailed specs on each component
6. **Keep it simple** - MVP first, then enhance

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | Check `__init__.py` exports |
| Ollama connection refused | Ensure `ollama serve` is running |
| Docker network issues | Use `host.docker.internal` for Ollama |
| Config not loading | Check file paths are relative to working dir |
| Circuit breaker stuck OPEN | Wait for recovery_timeout (30s) |
| npx not found | Install Node.js 20+ |
| Server won't start | Check `args` array in config, verify package exists |
| Server crashes immediately | Check stderr logs, may need env vars |
| Stdio bridge hangs | Ensure MCP server sends newline after JSON |
| Max restarts exceeded | Reset restart_count or increase max_restarts |
| Process zombie | Use `pkill -f` to clean up orphaned processes |
