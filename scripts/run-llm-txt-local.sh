#!/usr/bin/env bash
set -euo pipefail
# Wrapper to run server-llm-txt in local-mode against a checked-out llm-code-docs repo.
# Usage: run-llm-txt-local.sh [--transport http|stdio] [--port <port>]

# Default local docs path (can be overridden by exporting LLMSTXT_LOCAL_DIR beforehand)
: "${LLMSTXT_LOCAL_DIR:=${HOME}/Desktop/llm-code-docs}"
export LLMSTXT_LOCAL_DIR

NODE_MODULE_PATH="${HOME}/.local/share/mcps/node_modules/@mcp-get-community/server-llm-txt/dist/index.js"
exec node "${NODE_MODULE_PATH}" "$@"
