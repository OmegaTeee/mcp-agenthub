# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentHub is a centralized MCP (Model Context Protocol) router for macOS. It provides a single local endpoint (`localhost:9090`) that manages MCP servers, enhances prompts via Ollama, and provides resilience patterns.

## Development Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd mcps && npm install && cd ..

# Run router
uvicorn router.main:app --reload --port 9090

# Run tests
pytest tests/ -v

# Type checking
mypy router/

# Linting (ruff)
ruff check router/
ruff format router/

# Verify health
curl http://localhost:9090/health
```

## Architecture

This is a **modular monolith** built with FastAPI. The main package is `router/` with these modules:

| Module | Purpose |
|--------|---------|
| `config/` | Pydantic settings, JSON config loading |
| `servers/` | MCP server lifecycle (spawn, monitor, restart stdio processes) |
| `routing/` | MCP server registry, JSON-RPC proxy |
| `resilience/` | Circuit breaker (CLOSED → OPEN → HALF_OPEN states) |
| `cache/` | L1 in-memory LRU cache |
| `enhancement/` | Ollama HTTP client, per-client prompt enhancement |
| `dashboard/` | HTMX observability UI |
| `pipelines/` | Workflow orchestration (documentation generation) |
| `clients/` | Config generators for Claude Desktop, VS Code, Raycast |

### Request Flow

1. Request arrives at `/mcp/{server}/{path}`
2. Circuit breaker checked (reject if OPEN)
3. Server auto-started if configured with `auto_start: true`
4. JSON-RPC proxied via stdio bridge
5. Success/failure updates circuit breaker state

### Key Patterns

- **Pydantic Settings**: All config via `BaseSettings` with `.env` support
- **Async everywhere**: Use `httpx` (not `requests`), `asyncio` for I/O
- **Circuit breaker**: 3 failures → OPEN, 30s → HALF_OPEN, success → CLOSED
- **Stdio bridges**: MCP servers communicate via JSON-RPC over stdin/stdout

## Configuration Files

- `configs/mcp-servers.json` - MCP server registry (command, args, auto_start, restart_on_failure)
- `configs/enhancement-rules.json` - Per-client Ollama model selection and system prompts

## API Endpoints

```
GET  /health                    Health check
GET  /servers                   List all MCP servers
POST /servers/{name}/start      Start server
POST /servers/{name}/stop       Stop server
POST /mcp/{server}/{path}       Proxy JSON-RPC to MCP server
POST /ollama/enhance            Enhance prompt via Ollama (X-Client-Name header)
GET  /dashboard                 HTMX monitoring dashboard
POST /pipelines/documentation   Generate docs from codebase
```

## Code Style

- Python 3.11+ features, type hints required
- 88-char line limit (Black/ruff format)
- Use `logging` module, not `print()`
- Avoid global state; use dependency injection
- Never hardcode config; use Settings class
