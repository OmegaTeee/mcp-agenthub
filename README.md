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
| Phase 2 | **Complete** | Core router, caching, circuit breakers, Ollama enhancement |
| Phase 2.5 | **Complete** | MCP server management, stdio bridges |
| Phase 3 | **Complete** | Desktop integration, config generators, documentation pipeline |
| Phase 4 | **Complete** | HTMX dashboard with real-time monitoring |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for MCP servers)
- Docker Desktop or Colima
- Ollama running locally (`ollama serve`)

### Development
```bash
# Create virtual environment
python -m venv .venv && source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install MCP servers (Node.js packages)
cd mcps && npm install && cd ..

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
├── mcps/                   # Centralized MCP (Model Context Protocol) servers
│   ├── package.json        # npm dependencies for MCP servers
│   ├── node_modules/       # Installed npm packages (gitignored)
│   └── obsidian-mcp-tools/ # Obsidian vault integration (standalone binary)
├── router/                 # Python FastAPI application
├── configs/                # Runtime configuration
│   ├── mcp-servers.json    # MCP server registry (points to mcps/)
│   └── enhancement-rules.json
├── scripts/                # Shell wrapper scripts for API key management
│   ├── obsidian-mcp-tools.sh    # Obsidian MCP wrapper with Keychain integration
│   ├── validate-mcp-servers.sh  # MCP server validation utility
│   └── README.md                # Documentation for wrapper scripts
├── templates/              # Jinja2 templates for dashboard
├── tests/                  # Pytest test suite
├── guides/                 # User guides (Keychain, Figma, ComfyUI, etc.)
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

### User Guides
See `guides/` for integration guides:
- [Getting Started](guides/getting-started.md)
- [Keychain Setup](guides/keychain-setup.md)
- [LaunchAgent Setup](guides/launchagent-setup.md)
- [Figma Integration](guides/figma-integration.md)
- [ComfyUI Integration](guides/comfyui-integration.md)

## Key Features

### Prompt Enhancement
Each client (Claude, VS Code, Raycast) gets customized prompt enhancement:
- **Claude Desktop**: deepseek-r1 for structured reasoning
- **VS Code / Claude Code**: qwen3-coder for code-focused responses
- **Raycast**: deepseek-r1 for action-oriented responses
- **Obsidian**: deepseek-r1 with Markdown formatting

### Circuit Breakers
If an MCP server fails:
1. Circuit opens after 3 consecutive failures
2. Requests return fallback immediately (no hanging)
3. Circuit tests recovery after 30 seconds
4. Automatic restoration when service recovers

### Caching
- **L1**: Exact match (SHA256 hash) - instant response
- **L2**: Semantic similarity (Phase 2.1) - similar prompts hit cache

## Dashboard

Access the monitoring dashboard at:
```
http://localhost:9090/dashboard
```

Features:
- Service health status (auto-refresh every 5s)
- Cache stats and Ollama status (auto-refresh every 10s)
- Recent request activity (auto-refresh every 3s)
- Quick actions: clear cache, restart servers

## MCP Servers

AgentHub manages 7 MCP servers:

| Server | Package | Auto-Start | Description |
|--------|---------|------------|-------------|
| context7 | @upstash/context7-mcp | Yes | Documentation fetching |
| desktop-commander | @wonderwhy-er/desktop-commander | Yes | File operations |
| sequential-thinking | @modelcontextprotocol/server-sequential-thinking | Yes | Step-by-step reasoning |
| obsidian | obsidian-mcp-tools | Yes | Semantic search, templates for Obsidian vault |
| memory | @modelcontextprotocol/server-memory | No | Cross-session persistence |
| deepseek-reasoner | deepseek-reasoner-mcp | No | Local reasoning |
| fetch | mcp-fetch | No | HTTP fetch, GraphQL |

> See [configs/mcp-servers.json.examples](configs/mcp-servers.json.examples) for additional server examples including Python-based MCPs.

### Adding/Updating MCPs

**For npm packages:**
```bash
cd mcps
npm install <package-name>
# Update configs/mcp-servers.json with the new server
```

**For standalone binaries (like obsidian-mcp-tools):**
```bash
# Create directory
mkdir -p mcps/<mcp-name>/bin

# Copy binary
cp /path/to/binary mcps/<mcp-name>/bin/

# Create wrapper script (if API keys needed)
# See scripts/README.md for wrapper pattern
```

**For Python packages:**
```bash
# Add to requirements.txt
echo "<package-name>" >> requirements.txt

# Install in virtual environment
source .venv/bin/activate
pip install -r requirements.txt

# Create wrapper script (if API keys needed)
# See mcps/obsidian-mcp-tools/PYTHON-MCP-EXAMPLE.md for complete pattern
```

### API Key Management

MCP servers requiring API keys use wrapper scripts that retrieve credentials from macOS Keychain. See [scripts/README.md](scripts/README.md) for details.

**Add API keys to Keychain:**
```bash
security add-generic-password -a $USER -s obsidian_api_key -w YOUR_API_KEY
```

**Validate installation:**
```bash
./scripts/validate-mcp-servers.sh
```

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
