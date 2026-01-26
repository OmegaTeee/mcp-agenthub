# AgentHub Build Specification

> **Purpose**: Consolidated specification for building the AgentHub router
> **Target**: AI coding agents (Claude Code, Cursor, etc.)
> **Architecture**: Modular monolith with FastAPI

---

## Overview

AgentHub is a centralized MCP (Model Context Protocol) router that:
1. Unifies MCP server access across desktop apps (Claude, VS Code, Raycast, Obsidian)
2. Enhances prompts via local Ollama models before forwarding
3. Caches responses (L1 exact match, L2 semantic similarity)
4. Provides graceful degradation via circuit breakers

**Single endpoint**: `http://localhost:9090`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentHub Router                           │
├─────────────────────────────────────────────────────────────┤
│  config/          Load & validate JSON configs (Pydantic)    │
│  secrets/         macOS Keychain integration                 │
│  routing/         MCP server registry & proxy logic          │
│  resilience/      Circuit breaker pattern                    │
│  cache/           L1 (memory) + L2 (optional Qdrant)         │
│  enhancement/     Ollama prompt enhancement                  │
│  pipelines/       Workflow orchestration (Phase 3)           │
│  dashboard/       HTMX observability UI (Phase 4)            │
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
│   ├── routing/
│   │   ├── __init__.py
│   │   ├── registry.py          # ServerRegistry class
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

### MCP Proxy
```
POST /mcp/{server}/{path}       → Forward JSON-RPC to MCP server
                                  Example: POST /mcp/context7/tools/call
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
```json
{
  "servers": {
    "context7": {
      "url": "http://context7:3001",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "desktop-commander": {
      "url": "http://desktop-commander:3002",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "sequential-thinking": {
      "url": "http://sequential-thinking:3003",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "memory": {
      "url": "http://memory:3004",
      "transport": "http",
      "health_endpoint": "/health"
    }
  }
}
```

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
3. Check circuit breaker state
4. If OPEN, return fallback error
5. Forward JSON-RPC request via httpx
6. On success, reset circuit breaker
7. On failure, record failure in circuit breaker
8. Return response to client

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

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Ollama down | Return original prompt, log warning |
| MCP server down | Circuit breaker OPEN, return error JSON-RPC |
| Config file missing | Fail fast with clear error message |
| Invalid JSON-RPC | Return JSON-RPC error response |
| Timeout | Record failure in circuit breaker, return timeout error |

---

## References

See `reference/` folder for original phase documentation:
- `reference/docs/phase-1-vision.md` - Vision & goals
- `reference/docs/phase-2-core.md` - Original MVP spec
- `reference/docs/phase-3-integration.md` - Desktop integration
- `reference/docs/phase-4-dashboard.md` - Dashboard spec
