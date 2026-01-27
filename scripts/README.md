# MCP Server Scripts

This directory contains wrapper scripts for MCP servers that require API keys or special environment configuration.

## API Key Management Pattern

All API key wrapper scripts follow a secure pattern using macOS Keychain:

1. **Retrieve key from Keychain**: Uses `security find-generic-password` to securely fetch API keys
2. **Export as environment variable**: Sets the appropriate environment variable
3. **Exec the MCP server**: Replaces the shell process with the MCP server binary

### Example: Obsidian MCP Tools

```bash
#!/bin/bash
# Obsidian MCP Tools wrapper - loads API key from Keychain

OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Error: OBSIDIAN_API_KEY not found in Keychain" >&2
    echo "Add it with: security add-generic-password -a \$USER -s obsidian_api_key -w YOUR_KEY" >&2
    exit 1
fi

exec "${HOME}/.local/share/agenthub/mcps/obsidian-mcp-tools/bin/mcp-server" "$@"
```

## Adding API Keys to Keychain

For each MCP server that requires an API key:

```bash
# Obsidian
security add-generic-password -a $USER -s obsidian_api_key -w YOUR_API_KEY

# GitHub
security add-generic-password -a $USER -s github_api_key -w YOUR_API_KEY
```

## Available Scripts

| Script | Purpose |
|--------|---------|
| `obsidian-mcp-tools.sh` | Wrapper for Obsidian MCP server with API key from Keychain |
| `mcp-obsidian-rest.sh` | Example Python MCP wrapper (reference only, see PYTHON-MCP-EXAMPLE.md) |
| `mcp-obsidian.sh` | Legacy Obsidian MCP wrapper |
| `github-api-key.sh` | Template for GitHub API key wrapper |
| `validate-mcp-servers.sh` | Validates all configured MCP servers are installed correctly |
| `start-ollama.sh` | Starts Ollama service |
| `run-ollama-mcp.sh` | Runs Ollama MCP server |
| `run-llm-txt-local.sh` | Runs local LLM text service |
| `run-llm-txt-local-boot.sh` | LaunchAgent bootstrap for local LLM |
| `mcp-proxy.sh` | MCP proxy service wrapper |
| `mcp-proxy-restart.sh` | Restarts MCP proxy service |

## Validation

Run the validation script to check all MCP servers:

```bash
./scripts/validate-mcp-servers.sh
```

This will:
- Check if Node.js and npx are available
- Verify all Node.js MCP server files exist
- Run syntax checks on JavaScript files
- Check Python MCP servers are installed in venv
- Provide test commands for each server

## Integration with AgentHub

These wrapper scripts are referenced in [`configs/mcp-servers.json`](../configs/mcp-servers.json). For example:

```json
{
  "obsidian": {
    "package": "obsidian-mcp-tools",
    "transport": "stdio",
    "command": "./scripts/obsidian-mcp-tools.sh",
    "args": [],
    "env": {},
    "auto_start": true,
    "restart_on_failure": true,
    "max_restarts": 3,
    "health_check_interval": 30,
    "description": "Semantic search, templates, and file management for Obsidian vault"
  }
}
```

## Security Best Practices

1. **Never commit API keys**: Always use Keychain or environment variables
2. **Use restrictive permissions**: Wrapper scripts should be readable/executable only by the user
3. **Validate keys exist**: Always check if the key was retrieved successfully before executing
4. **Use exec**: Replace the shell process to avoid leaving sensitive data in process memory
