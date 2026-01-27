#!/bin/bash
# MCP Proxy wrapper - loads API keys from Keychain and starts the proxy

# Load Obsidian API key
OBSIDIAN_API_KEY="$(security find-generic-password -a "${USER}" -s "obsidian_api_key" -w 2>/dev/null)"
export OBSIDIAN_API_KEY
if [[ -z "${OBSIDIAN_API_KEY}" ]]; then
    echo "Warning: OBSIDIAN_API_KEY not found in Keychain (Obsidian tools will be unavailable)" >&2
fi

# Start the proxy
exec "${HOME}/go/bin/mcp-proxy" --config "${HOME}/.local/share/mcps/proxy-config.json" "$@"
