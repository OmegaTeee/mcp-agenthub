# Obsidian MCP Tools

MCP (Model Context Protocol) server for Obsidian vault integration.

## About

This is the [mcp-tools](https://github.com/MarkusPfundstein/mcp-obsidian) Obsidian plugin, extracted as a standalone MCP server. It provides semantic search, templates, and file management capabilities for your Obsidian vault.

**Version**: 0.2.27
**Author**: Jack Steam
**Source**: https://github.com/jacksteamdev

## Installation

The binary (`bin/mcp-server`) is a compiled ARM64 macOS executable built with Bun. It was copied from:
```
~/Obsidian/.obsidian/plugins/mcp-tools/bin/mcp-server
```

## Usage

This server is configured to run through a wrapper script that loads the API key from macOS Keychain:

```bash
../../scripts/obsidian-mcp-tools.sh
```

The wrapper script:
1. Retrieves `OBSIDIAN_API_KEY` from Keychain
2. Exports it as an environment variable
3. Executes the `bin/mcp-server` binary

## Configuration

### Add API Key to Keychain

```bash
security add-generic-password -a $USER -s obsidian_api_key -w YOUR_API_KEY
```

### MCP Server Configuration

This server is configured in [`../../configs/mcp-servers.json`](../../configs/mcp-servers.json):

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

## Capabilities

- **Semantic Search**: Search your vault with natural language queries
- **File Management**: Read, write, and manage Obsidian notes
- **Templates**: Execute Obsidian templates programmatically
- **Vault Operations**: List files, search vault, patch content

## Upgrading

To upgrade to a newer version:

1. Update the Obsidian plugin in Obsidian
2. Copy the new binary:
   ```bash
   cp ~/Obsidian/.obsidian/plugins/mcp-tools/bin/mcp-server ./bin/
   chmod +x ./bin/mcp-server
   ```
3. Update the version in this README

## Testing

Test the installation:

```bash
../../scripts/obsidian-mcp-tools.sh --version
```

Should output: `0.2.27`
