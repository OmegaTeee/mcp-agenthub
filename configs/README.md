# AgentHub Configuration Files

This folder contains all configuration files for AgentHub and client integrations.

## Directory Structure

```
configs/
├── README.md                              # This file
├── clients/                               # Client-specific configurations
│   ├── README.md                          # Client configs overview
│   ├── claude/                            # Claude Desktop
│   │   ├── README.md
│   │   ├── claude-desktop-unified.json    # Recommended: Unified MCP bridge
│   │   ├── claude-desktop-config.json.example
│   │   └── claude_desktop_config.json     # Symlink to actual config
│   ├── raycast/                           # Raycast
│   │   ├── README.md
│   │   └── raycast-mcp-servers.json.example
│   └── vscode/                            # VS Code / Claude Code / Cline
│       ├── README.md
│       ├── vscode-settings.json.example
│       └── vscode.json                    # Full workspace config
├── enhancement-rules.json                 # AgentHub: Prompt enhancement rules
├── mcp-servers.json                       # AgentHub: MCP server registry
├── mcp-servers-keyring.json.example       # AgentHub: Credential management
├── logrotate.conf                         # System: Log rotation (Linux)
└── logrotate-macos.conf                   # System: Log rotation (macOS)
```

## Configuration Types

### 🎯 Client Configurations (`clients/`)
Application-specific settings for connecting to AgentHub:
- Claude Desktop: MCP server configuration
- VS Code: Workspace settings and tasks
- Raycast: Script commands and shortcuts

**When to modify:** Setting up a new client or changing connection settings.

### ⚙️ AgentHub Configurations (root)
Core AgentHub router settings:
- **`enhancement-rules.json`** - Per-client Ollama models and system prompts
- **`mcp-servers.json`** - MCP server lifecycle (command, args, auto_start)
- **`mcp-servers-keyring.json.example`** - Secure credential storage

**When to modify:** Adding MCP servers, changing enhancement behavior, or managing credentials.

### 🔧 System Configurations (root)
Infrastructure and logging:
- **`logrotate.conf`** - Log file rotation and archival
- **`logrotate-macos.conf`** - macOS-specific log rotation

**When to modify:** Adjusting log retention policies or disk space management.

## Quick Links

### Setting Up a Client
1. **Claude Desktop** → [clients/claude/README.md](clients/claude/README.md)
2. **VS Code** → [clients/vscode/README.md](clients/vscode/README.md)
3. **Raycast** → [clients/raycast/README.md](clients/raycast/README.md)

### Common Tasks

**Add a new MCP server:**

```bash
# Edit the registry
vim configs/mcp-servers.json

# Add entry like:
{
  "my-server": {
    "command": "npx",
    "args": ["-y", "@org/my-mcp-server"],
    "auto_start": true,
    "restart_on_failure": true,
    "max_restart_delay_seconds": 300
  }
}
```

**Change enhancement model:**

```bash
# Edit enhancement rules
vim configs/enhancement-rules.json

# Modify client-specific model:
{
  "vscode": {
    "model": "qwen3-coder:latest",  # Change to your preferred model
    "system_prompt": "..."
  }
}
```

**Configure credentials:**

```bash
# Copy example
cp configs/mcp-servers-keyring.json.example configs/mcp-servers-keyring.json

# Add credentials (automatically stored in macOS Keychain)
vim configs/mcp-servers-keyring.json
```

## Configuration Philosophy

This organization separates:

1. **Client concerns** (how apps connect) → `clients/`
2. **Router concerns** (how AgentHub behaves) → root
3. **System concerns** (logging, OS integration) → root

This makes it easy to:
- ✅ Add new clients without touching AgentHub config
- ✅ Modify AgentHub behavior without breaking clients
- ✅ Share client configs with team members
- ✅ Version control client and router configs separately

## Environment Variables

AgentHub supports environment variable overrides:

```bash
# Override router port
ROUTER_PORT=8080 uvicorn router.main:app

# Override MCP config location
MCP_CONFIG_PATH=/custom/path/mcp-servers.json uvicorn router.main:app

# Override enhancement config
ENHANCEMENT_CONFIG_PATH=/custom/path/enhancement-rules.json uvicorn router.main:app
```

## Best Practices

### Version Control

```bash
# Track AgentHub configs
git add configs/enhancement-rules.json
git add configs/mcp-servers.json

# Ignore client-specific customizations
echo "configs/clients/*/local-*.json" >> .gitignore
```

### Secrets Management

```bash
# Never commit credentials
git add configs/mcp-servers-keyring.json.example  # Example only
echo "configs/mcp-servers-keyring.json" >> .gitignore  # Actual secrets
```

### Backup

```bash
# Backup all configs
tar -czf agenthub-configs-$(date +%Y%m%d).tar.gz configs/

# Restore
tar -xzf agenthub-configs-20260130.tar.gz
```

## Documentation

For detailed setup and usage:
- [Integration Guides](../guides/)
- [Testing Integrations](../guides/testing-integrations.md)
- [Keyring Migration Guide](../guides/keyring-migration-guide.md)
