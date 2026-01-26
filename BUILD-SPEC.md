# AgentHub Build Specification

> **Purpose**: Consolidated specification for building the AgentHub router
> **Target**: AI coding agents (Claude Code, Cursor, etc.)
> **Architecture**: Modular monolith with FastAPI

---

## Overview

AgentHub is a centralized MCP (Model Context Protocol) hub that:
1. **Manages MCP servers** - Installs, starts, stops, and supervises MCP server processes
2. **Unifies access** across desktop apps (Claude, VS Code, Raycast, Obsidian)
3. **Enhances prompts** via local Ollama models before forwarding
4. **Caches responses** (L1 exact match, L2 semantic similarity)
5. **Provides resilience** via circuit breakers and auto-restart

**Single endpoint**: `http://localhost:9090`

**Key Capability**: Full lifecycle management of stdio-based MCP servers with automatic health monitoring and restart.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentHub Router                          │
├─────────────────────────────────────────────────────────────┤
│  config/          Load & validate JSON configs (Pydantic)   │
│  secrets/         macOS Keychain integration                │
│  servers/         MCP server lifecycle management (NEW)     │
│  routing/         MCP server registry & proxy logic         │
│  resilience/      Circuit breaker pattern                   │
│  cache/           L1 (memory) + L2 (optional Qdrant)        │
│  enhancement/     Ollama prompt enhancement                 │
│  pipelines/       Workflow orchestration (Phase 3)          │
│  dashboard/       HTMX observability UI (Phase 4)           │
└─────────────────────────────────────────────────────────────┘
         │
         │ Manages
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Processes                     │
├─────────────────────────────────────────────────────────────┤
│  context7          (stdio)  Auto-started, supervised        │
│  desktop-commander (stdio)  Auto-started, supervised        │
│  sequential-thinking (stdio) Auto-started, supervised       │
│  memory            (stdio)  Auto-started, supervised        │
│  [custom servers]  (stdio)  User-configured                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
agenthub/
├── router/                      # Main Python package
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Pydantic settings model
│   │   └── loader.py            # Load mcp-servers.json, enhancement-rules.json
│   ├── secrets/
│   │   ├── __init__.py
│   │   └── keychain.py          # macOS Keychain via `keyring` or subprocess
│   ├── servers/                 # MCP server lifecycle management
│   │   ├── __init__.py
│   │   ├── models.py            # ServerConfig, ServerStatus, ProcessInfo
│   │   ├── registry.py          # ServerRegistry - track configs and running processes
│   │   ├── installer.py         # Install MCP packages via npm/npx
│   │   ├── process.py           # Spawn and manage subprocess lifecycle
│   │   ├── bridge.py            # Stdio ↔ JSON-RPC protocol bridge
│   │   └── supervisor.py        # Health monitoring, auto-restart logic
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── registry.py          # ServerRegistry class (delegates to servers/)
│   │   └── proxy.py             # Forward JSON-RPC to MCP servers
│   ├── resilience/
│   │   ├── __init__.py
│   │   └── circuit_breaker.py   # CircuitBreaker with CLOSED/OPEN/HALF_OPEN
│   ├── cache/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract cache interface
│   │   ├── memory.py            # In-memory LRU cache
│   │   └── qdrant.py            # Qdrant vector cache (Phase 2.1, optional)
│   ├── enhancement/
│   │   ├── __init__.py
│   │   ├── middleware.py        # FastAPI middleware for prompt enhancement
│   │   └── ollama.py            # Ollama HTTP client
│   ├── pipelines/
│   │   ├── __init__.py
│   │   └── documentation.py     # Documentation generation pipeline
│   ├── dashboard/
│   │   ├── __init__.py
│   │   ├── routes.py            # Dashboard endpoints
│   │   └── stats.py             # CacheStats, ActivityLog classes
│   └── middleware/
│       ├── __init__.py
│       └── logging.py           # Request/response activity logging
├── templates/                   # Jinja2 templates for dashboard
│   ├── dashboard.html
│   └── partials/
│       ├── health.html
│       ├── stats.html
│       └── activity.html
├── configs/                     # Runtime configuration (JSON)
│   ├── mcp-servers.json         # MCP server registry
│   └── enhancement-rules.json   # Per-client enhancement rules
├── scripts/                     # Shell utilities (existing)
├── tests/                       # Pytest test suite
│   ├── __init__.py
│   ├── test_routing.py
│   ├── test_cache.py
│   ├── test_circuit_breaker.py
│   └── test_enhancement.py
├── docker-compose.yml           # Service orchestration
├── Dockerfile                   # Router container image
├── pyproject.toml               # Python project config
├── requirements.txt             # Python dependencies
└── README.md                    # User-facing documentation
```

---

## API Endpoints

### Health & Status
```
GET  /health                    → All services status
GET  /health/{server}           → Single server status
```

### Server Management (NEW)
```
GET    /servers                 → List all servers with status
GET    /servers/{name}          → Get server details + process status
POST   /servers/{name}/start    → Start a server process
POST   /servers/{name}/stop     → Stop a server process
POST   /servers/{name}/restart  → Restart a server process
POST   /servers/install         → Install a new MCP package
                                  Body: {"package": "@org/mcp-server", "name": "custom-name"}
DELETE /servers/{name}          → Remove a server from config
```

### MCP Proxy
```
POST /mcp/{server}/{path}       → Forward JSON-RPC to MCP server
                                  Example: POST /mcp/context7/tools/call
                                  Note: Auto-starts server if configured with auto_start=true
```

### Enhancement (Direct)
```
POST /ollama/enhance            → Enhance a prompt via Ollama
                                  Headers: X-Client-Name (optional)
                                  Body: {"prompt": "..."}
```

### Pipelines (Phase 3)
```
POST /pipelines/documentation   → Generate docs from codebase
                                  Body: {"repo_path": "...", "project_name": "..."}
```

### Dashboard (Phase 4)
```
GET  /dashboard                 → Main dashboard HTML page
GET  /dashboard/health-partial  → HTMX partial: service health
GET  /dashboard/stats-partial   → HTMX partial: cache stats
GET  /dashboard/activity-partial→ HTMX partial: recent requests
POST /dashboard/actions/clear-cache
POST /dashboard/actions/restart/{server}
```

---

## Configuration Files

### configs/mcp-servers.json

**New schema with process management support:**

```json
{
  "servers": {
    "context7": {
      "package": "@upstash/context7-mcp",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "env": {},
      "auto_start": true,
      "restart_on_failure": true,
      "max_restarts": 3,
      "health_check_interval": 30,
      "description": "Documentation fetching from libraries"
    },
    "desktop-commander": {
      "package": "@wonderwhy-er/desktop-commander",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@wonderwhy-er/desktop-commander"],
      "env": {},
      "auto_start": true,
      "restart_on_failure": true,
      "description": "File operations and terminal commands"
    },
    "sequential-thinking": {
      "package": "@modelcontextprotocol/server-sequential-thinking",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "auto_start": true,
      "description": "Step-by-step reasoning and planning"
    },
    "memory": {
      "package": "@modelcontextprotocol/server-memory",
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "auto_start": true,
      "description": "Cross-session context persistence"
    }
  }
}
```

**Configuration Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `package` | string | Yes | npm package name |
| `transport` | string | Yes | `stdio` or `http` |
| `command` | string | Yes* | Command to run (`npx`, `node`, `python`) |
| `args` | array | Yes* | Command arguments |
| `env` | object | No | Environment variables for process |
| `auto_start` | bool | No | Start on router startup (default: false) |
| `restart_on_failure` | bool | No | Auto-restart crashed processes (default: true) |
| `max_restarts` | int | No | Max restarts before giving up (default: 3) |
| `health_check_interval` | int | No | Seconds between health checks (default: 30) |
| `url` | string | No* | For http transport, the server URL |
| `description` | string | No | Human-readable description |

*Required for `stdio` transport: `command`, `args`
*Required for `http` transport: `url`

### configs/enhancement-rules.json
```json
{
  "default": {
    "enabled": true,
    "model": "llama3.2:3b",
    "system_prompt": "Improve clarity and structure. Preserve intent. Return only the enhanced prompt."
  },
  "clients": {
    "claude-desktop": {
      "model": "deepseek-r1:14b",
      "system_prompt": "Provide structured responses with clear reasoning. Use Markdown."
    },
    "vscode": {
      "model": "qwen2.5-coder:7b",
      "system_prompt": "Code-first responses. Include file paths. Minimal prose."
    },
    "raycast": {
      "model": "llama3.2:3b",
      "system_prompt": "Action-oriented. Suggest CLI commands. Under 200 words."
    },
    "obsidian": {
      "model": "llama3.2:3b",
      "system_prompt": "Format in Markdown. Use [[wikilinks]] and #tags."
    }
  },
  "fallback_chain": ["phi3:mini", null]
}
```

---

## Core Components

### 1. Settings (config/settings.py)

```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 9090

    # Ollama
    ollama_host: str = "host.docker.internal"
    ollama_port: int = 11434

    # Cache
    cache_max_size: int = 1000
    cache_similarity_threshold: float = 0.85

    # Circuit Breaker
    cb_failure_threshold: int = 3
    cb_recovery_timeout: int = 30

    # Paths
    mcp_servers_config: str = "configs/mcp-servers.json"
    enhancement_rules_config: str = "configs/enhancement-rules.json"

    class Config:
        env_file = ".env"
        env_prefix = ""
```

### 2. Circuit Breaker (resilience/circuit_breaker.py)

States:
- **CLOSED**: Service healthy, forward requests normally
- **OPEN**: Service broken, reject requests immediately, return fallback
- **HALF_OPEN**: Testing recovery, allow one request through

Transitions:
- CLOSED → OPEN: After `failure_threshold` consecutive failures
- OPEN → HALF_OPEN: After `recovery_timeout` seconds
- HALF_OPEN → CLOSED: If test request succeeds
- HALF_OPEN → OPEN: If test request fails

### 3. Cache (cache/memory.py)

**L1 Cache (Exact Match)**:
- Key: SHA256 hash of prompt text
- Value: Enhanced prompt
- Eviction: LRU when size > `cache_max_size`

**L2 Cache (Semantic Similarity)** - Phase 2.1:
- Key: Embedding vector (nomic-embed-text)
- Match: Cosine similarity > `cache_similarity_threshold`
- Storage: Qdrant vector database

### 4. Enhancement Middleware (enhancement/middleware.py)

Flow:
1. Extract `X-Client-Name` header (default: "default")
2. Look up enhancement rules for client
3. Check L1 cache for exact match
4. If miss, call Ollama with client-specific model + system prompt
5. Cache result
6. Return enhanced prompt

Fallback:
- If Ollama fails, return original prompt (unenhanced)
- Log the failure for debugging

### 5. MCP Proxy (routing/proxy.py)

Flow:
1. Parse `{server}` from URL path
2. Look up server in registry
3. **If server not running and auto_start=true, start it**
4. Check circuit breaker state
5. If OPEN, return fallback error
6. Forward JSON-RPC request via stdio bridge or httpx
7. On success, reset circuit breaker
8. On failure, record failure in circuit breaker
9. Return response to client

### 6. Server Manager (servers/) - NEW

The servers module provides full lifecycle management for MCP servers.

#### Models (servers/models.py)

```python
from enum import Enum
from pydantic import BaseModel

class ServerTransport(str, Enum):
    STDIO = "stdio"
    HTTP = "http"

class ServerStatus(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    STOPPING = "stopping"

class ServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str
    package: str
    transport: ServerTransport
    command: str | None = None
    args: list[str] = []
    env: dict[str, str] = {}
    url: str | None = None  # For HTTP transport
    auto_start: bool = False
    restart_on_failure: bool = True
    max_restarts: int = 3
    health_check_interval: int = 30
    description: str = ""

class ProcessInfo(BaseModel):
    """Runtime information about a server process."""
    pid: int | None = None
    status: ServerStatus = ServerStatus.STOPPED
    started_at: float | None = None
    restart_count: int = 0
    last_error: str | None = None
```

#### Registry (servers/registry.py)

```python
class ServerRegistry:
    """Manages server configurations and running processes."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.servers: dict[str, ServerConfig] = {}
        self.processes: dict[str, ProcessInfo] = {}

    def load(self) -> None:
        """Load server configs from JSON file."""

    def save(self) -> None:
        """Save server configs to JSON file."""

    def get(self, name: str) -> ServerConfig | None:
        """Get a server config by name."""

    def list_all(self) -> list[tuple[ServerConfig, ProcessInfo]]:
        """List all servers with their process info."""

    def add(self, config: ServerConfig) -> None:
        """Add a new server configuration."""

    def remove(self, name: str) -> None:
        """Remove a server configuration."""
```

#### Process Manager (servers/process.py)

```python
class ProcessManager:
    """Manages subprocess lifecycle for stdio MCP servers."""

    async def start(self, config: ServerConfig) -> ProcessInfo:
        """Start a server process."""
        # 1. Spawn subprocess with config.command + config.args
        # 2. Set up stdio pipes
        # 3. Return ProcessInfo with PID

    async def stop(self, name: str) -> None:
        """Stop a server process gracefully."""
        # 1. Send SIGTERM
        # 2. Wait for graceful shutdown
        # 3. Send SIGKILL if needed

    async def restart(self, name: str) -> ProcessInfo:
        """Restart a server process."""
```

#### Stdio Bridge (servers/bridge.py)

```python
class StdioBridge:
    """Bridges HTTP JSON-RPC to stdio JSON-RPC."""

    def __init__(self, process: asyncio.subprocess.Process):
        self.process = process
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}

    async def send(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and wait for response."""
        # 1. Write JSON-RPC to stdin
        # 2. Read response from stdout
        # 3. Match by request ID
        # 4. Return result or raise error

    async def _read_loop(self) -> None:
        """Background task to read responses from stdout."""
```

#### Supervisor (servers/supervisor.py)

```python
class Supervisor:
    """Monitors server health and handles auto-restart."""

    def __init__(self, registry: ServerRegistry, process_manager: ProcessManager):
        self.registry = registry
        self.process_manager = process_manager
        self._running = False

    async def start(self) -> None:
        """Start supervisor background task."""
        # 1. Start all auto_start servers
        # 2. Begin health check loop

    async def stop(self) -> None:
        """Stop supervisor and all managed servers."""

    async def _health_check_loop(self) -> None:
        """Periodically check server health."""
        # For each running server:
        # 1. Check if process is alive
        # 2. If dead and restart_on_failure, restart
        # 3. If restart_count > max_restarts, mark as FAILED
```

---

## Dependencies

### Python (requirements.txt)
```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
httpx>=0.26.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
jinja2>=3.1.0
python-multipart>=0.0.6
keyring>=24.0.0
```

### Optional (Phase 2.1+)
```
qdrant-client>=1.7.0
```

---

## Environment Variables

```bash
# Server
ROUTER_HOST=0.0.0.0
ROUTER_PORT=9090

# Ollama
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
OLLAMA_MODEL=deepseek-r1:latest

# Cache
CACHE_MAX_SIZE=1000
CACHE_SIMILARITY_THRESHOLD=0.85

# Circuit Breaker
CB_FAILURE_THRESHOLD=3
CB_RECOVERY_TIMEOUT=30

# Logging
LOG_LEVEL=info

# Secrets (loaded from Keychain)
OBSIDIAN_API_KEY=
GITHUB_TOKEN=
```

---

## Testing Requirements

Each module should have corresponding tests:

1. **test_routing.py**: Registry loads, proxy forwards correctly, unknown servers return 404
2. **test_cache.py**: L1 hits/misses, LRU eviction works, stats tracking
3. **test_circuit_breaker.py**: State transitions, recovery timeout, failure counting
4. **test_enhancement.py**: Client rules applied, fallback on Ollama failure, caching works

Run with: `pytest tests/ -v`

---

## Success Criteria

### Phase 2 (MVP) - Must Have
- [ ] Router starts with `uvicorn router.main:app`
- [ ] `GET /health` returns all services status
- [ ] `POST /mcp/{server}/tools/call` proxies to MCP servers
- [ ] `POST /ollama/enhance` returns enhanced prompts
- [ ] Circuit breaker activates after 3 failures
- [ ] Circuit breaker recovers after 30 seconds
- [ ] L1 cache reduces duplicate Ollama calls
- [ ] Configs are hot-reloadable (restart applies changes)

### Phase 2.5 (Server Management) - Must Have
- [ ] `GET /servers` lists all configured servers with status
- [ ] `POST /servers/{name}/start` starts a stopped server
- [ ] `POST /servers/{name}/stop` stops a running server
- [ ] Stdio bridge correctly handles JSON-RPC over stdio
- [ ] Supervisor auto-starts servers with `auto_start: true`
- [ ] Supervisor auto-restarts crashed servers
- [ ] Supervisor respects `max_restarts` limit
- [ ] `POST /servers/install` installs new MCP packages

### Phase 3 (Integration) - Should Have
- [ ] Claude Desktop connects via proxy
- [ ] VS Code uses qwen2.5-coder model for enhancement
- [ ] Documentation pipeline generates markdown to Obsidian

### Phase 4 (Dashboard) - Nice to Have
- [ ] Dashboard loads at `/dashboard`
- [ ] HTMX partials update every 5-10 seconds
- [ ] Clear cache button works
- [ ] Activity log shows recent requests

---

## Non-Goals

- No user authentication (local-only, OS provides auth)
- No internet exposure (localhost only)
- No database for MVP (in-memory cache is sufficient)
- No React/Vue (HTMX for dashboard)
- No Kubernetes (Docker Compose is sufficient)
- No GUI for server management (API + dashboard only)
- No automatic package updates (manual reinstall required)

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Ollama down | Return original prompt, log warning |
| MCP server down | Circuit breaker OPEN, return error JSON-RPC |
| Config file missing | Fail fast with clear error message |
| Invalid JSON-RPC | Return JSON-RPC error response |
| Timeout | Record failure in circuit breaker, return timeout error |
| Server process crash | Auto-restart if `restart_on_failure` enabled |
| Max restarts exceeded | Mark server as FAILED, stop restart attempts |
| npm/npx not found | Return clear error, require Node.js installation |
| Package install fails | Return npm error message, suggest manual install |
| Server won't start | Log error, mark as FAILED, include stderr in response |

---

## References

See `reference/` folder for original phase documentation:
- `reference/docs/phase-1-vision.md` - Vision & goals
- `reference/docs/phase-2-core.md` - Original MVP spec
- `reference/docs/phase-3-integration.md` - Desktop integration
- `reference/docs/phase-4-dashboard.md` - Dashboard spec
