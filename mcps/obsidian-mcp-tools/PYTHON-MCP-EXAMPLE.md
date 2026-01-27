# Python MCP Server Example: mcp-obsidian

This guide demonstrates how to add Python-based MCP servers to AgentHub, using `mcp-obsidian` as a reference implementation.

> **Note**: The `obsidian-mcp-tools` (plugin-based) server is the primary Obsidian integration. This Python alternative is documented as an **example** for adding other Python MCP servers in the future.

---

## Why This is an Example

The Python-based `mcp-obsidian` doesn't add significant value over the plugin-based version because:
- ❌ No semantic search capabilities
- ❌ No Templater integration
- ✅ Only provides basic REST API file operations

However, it serves as a **great reference** for integrating other Python MCP servers that provide unique functionality.

---

## Installation Pattern for Python MCP Servers

### 1. Add to requirements.txt

```bash
# requirements.txt
# MCP Servers (Python-based) - Examples only, uncomment to use
# mcp-obsidian>=0.1.0  # Example: Obsidian via REST API (requires Local REST API plugin)
```

### 2. Install in Virtual Environment

```bash
source .venv/bin/activate
pip install mcp-obsidian
```

### 3. Create Wrapper Script (if API keys needed)

Create `scripts/<mcp-name>.sh`:

```bash
#!/bin/bash
# MCP wrapper - loads API key from Keychain

API_KEY="$(security find-generic-password -a "${USER}" -s "<keychain_service>" -w 2>/dev/null)"
export API_KEY
if [[ -z "${API_KEY}" ]]; then
    echo "Error: API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s <keychain_service> -w YOUR_KEY" >&2
    exit 1
fi

# Set other environment variables
export OTHER_ENV_VAR="value"

# Activate virtual environment and run MCP server
AGENTHUB_DIR="${HOME}/.local/share/agenthub"
source "${AGENTHUB_DIR}/.venv/bin/activate"
exec python -m <module_name> "$@"
```

Make it executable:
```bash
chmod +x scripts/<mcp-name>.sh
```

### 4. Add to mcp-servers.json

```json
{
  "servers": {
    "<mcp-name>": {
      "package": "<python-package-name>",
      "transport": "stdio",
      "command": "./scripts/<mcp-name>.sh",
      "args": [],
      "env": {},
      "auto_start": false,
      "restart_on_failure": true,
      "max_restarts": 3,
      "health_check_interval": 30,
      "description": "What this MCP server does"
    }
  }
}
```

### 5. Update Validation Script

Add Python package check to `scripts/validate-mcp-servers.sh`:

```bash
# Check Python MCP servers
if "${AGENTHUB_DIR}/.venv/bin/pip" show <package-name> &>/dev/null; then
  echo "FOUND: <package-name> (Python package)"
  "${AGENTHUB_DIR}/.venv/bin/pip" show <package-name> | grep "Version:"
else
  echo "MISSING: <package-name> (Python package)"
fi
```

---

## mcp-obsidian Specific Setup (Reference)

### Requirements
1. Obsidian running with [Local REST API plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
2. REST API on port `27124`
3. API key in macOS Keychain

### Wrapper Script

See `scripts/mcp-obsidian-rest.sh`:

```bash
#!/bin/bash
OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: OBSIDIAN_API_KEY not found in Keychain" >&2
    exit 1
fi

OBSIDIAN_HOST="https://127.0.0.1"
export OBSIDIAN_HOST

OBSIDIAN_PORT="27124"
export OBSIDIAN_PORT

AGENTHUB_DIR="${HOME}/.local/share/agenthub"
source "${AGENTHUB_DIR}/.venv/bin/activate"
exec python -m mcp_obsidian "$@"
```

### Configuration

See `configs/mcp-servers.json.examples`:

```json
{
  "obsidian-rest": {
    "package": "mcp-obsidian",
    "transport": "stdio",
    "command": "./scripts/mcp-obsidian-rest.sh",
    "args": [],
    "env": {},
    "auto_start": false,
    "restart_on_failure": true,
    "max_restarts": 3,
    "health_check_interval": 30,
    "description": "Obsidian vault integration via REST API (requires Local REST API plugin)"
  }
}
```

---

## When to Use Python MCP Servers

Consider Python MCP servers when:
- ✅ The MCP server is only available as a Python package
- ✅ You need to integrate with Python-specific libraries
- ✅ The server provides unique functionality not available in npm packages
- ✅ You want to write custom Python-based MCP tools

Examples of good use cases:
- Scientific computing tools (NumPy, Pandas, matplotlib)
- ML/AI frameworks (Hugging Face, PyTorch)
- Python-first APIs (OpenAI Python SDK, Anthropic Python SDK)
- Custom data processing pipelines

---

## References

- [MarkusPfundstein/mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) - Python/REST API server
- [Local REST API Plugin](https://github.com/coddingtonbear/obsidian-local-rest-api) - Required for mcp-obsidian
- [Model Context Protocol](https://modelcontextprotocol.io) - Official MCP specification
- [configs/mcp-servers.json.examples](../../configs/mcp-servers.json.examples) - Example configurations
