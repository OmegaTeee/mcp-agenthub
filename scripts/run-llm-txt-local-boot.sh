#!/usr/bin/env bash
set -euo pipefail
# Robust boot script for server-llm-txt local mode.
# Ensures PATH and env are set before exec'ing the adapter.

# Known Homebrew locations + standard system paths
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"

# Ensure HOME is set
HOME_DIR="${HOME:-/Users/visualval}"

# Default local docs dir (can be overridden by environment)
export LLMSTXT_LOCAL_DIR="${LLMSTXT_LOCAL_DIR:-${HOME_DIR}/projects/llm-code-docs}"

# Adapter JS entry
ADAPTER_JS="${HOME_DIR}/.local/share/mcps/node_modules/@mcp-get-community/server-llm-txt/dist/index.js"

if [[ ! -f "${ADAPTER_JS}" ]]; then
  echo "Adapter not found: ${ADAPTER_JS}" >&2
  exit 2
fi

# Exec node from PATH (allow shell to resolve user's node install)
exec node "${ADAPTER_JS}"