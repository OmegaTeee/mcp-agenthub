# AgentHub

Lightweight local-first AI agent hub for macOS — central router, prompt enhancement, and desktop integrations.

## Overview

AgentHub provides a single local router (`localhost:9090`) that:
- Manages MCP servers centrally (configure once, use everywhere)
- Enhances prompts via Ollama before forwarding to AI services
- Provides circuit breakers for graceful degradation
- Caches responses for performance

**Target clients**: Claude Desktop, VS Code, Raycast, Obsidian, ComfyUI

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 2 | **In Progress** | Core router MVP |
| Phase 3 | Planned | Desktop integration |
| Phase 4 | Planned | Dashboard (optional) |

## Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop or Colima
- Ollama running locally (`ollama serve`)

### Development
```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run router (once built)
uvicorn router.main:app --reload --port 9090

# Verify health
curl http://localhost:9090/health
```

### Docker
```bash
docker compose up -d
curl http://localhost:9090/health
```

## Project Structure

```
agenthub/
├── BUILD-SPEC.md           # Consolidated build specification (START HERE)
├── BUILD-TASKS.md          # Step-by-step build checklist
├── router/                 # Python FastAPI application (to be built)
├── configs/                # Runtime configuration
│   ├── mcp-servers.json    # MCP server registry
│   └── enhancement-rules.json
├── scripts/                # Shell utilities
├── templates/              # Jinja2 templates for dashboard
├── tests/                  # Pytest test suite
├── reference/              # Historical documentation
│   └── docs/               # Original phase docs (for context)
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Build Documentation

| Document | Purpose |
|----------|---------|
| [BUILD-SPEC.md](BUILD-SPEC.md) | **Consolidated specification** - Architecture, endpoints, components |
| [BUILD-TASKS.md](BUILD-TASKS.md) | **Step-by-step checklist** - Module-by-module build tasks |

### For AI Agents
Start with `BUILD-SPEC.md` for architecture understanding, then follow `BUILD-TASKS.md` sequentially.

### Reference Documentation
Original phase documentation is preserved in `reference/docs/` for additional context:
- `reference/docs/phase-1-vision.md` - Original vision & goals
- `reference/docs/phase-2-core.md` - Original MVP spec
- `reference/docs/phase-3-integration.md` - Desktop integration details
- `reference/docs/phase-4-dashboard.md` - Dashboard specifications
- `reference/docs/user-guide/` - Integration guides (Keychain, Figma, etc.)

## Key Features

### Prompt Enhancement
Each client (Claude, VS Code, Raycast) gets customized prompt enhancement:
- **Claude Desktop**: deepseek-r1 for structured reasoning
- **VS Code**: qwen2.5-coder for code-focused responses
- **Raycast**: llama3.2 for fast, action-oriented responses

### Circuit Breakers
If an MCP server fails:
1. Circuit opens after 3 consecutive failures
2. Requests return fallback immediately (no hanging)
3. Circuit tests recovery after 30 seconds
4. Automatic restoration when service recovers

### Caching
- **L1**: Exact match (SHA256 hash) - instant response
- **L2**: Semantic similarity (Phase 2.1) - similar prompts hit cache

## Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:
```bash
OLLAMA_HOST=host.docker.internal
OLLAMA_PORT=11434
ROUTER_PORT=9090
```

### MCP Servers
Edit `configs/mcp-servers.json` to add/remove MCP servers.

### Enhancement Rules
Edit `configs/enhancement-rules.json` to customize per-client behavior.

## Contributing

1. Read `BUILD-SPEC.md` to understand the architecture
2. Follow `BUILD-TASKS.md` for implementation
3. Submit PRs against `main`

## License

MIT License - See [LICENSE](LICENSE)
