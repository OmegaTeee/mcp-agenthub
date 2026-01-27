#!/usr/bin/env bash
set -euo pipefail
# Wrapper to run the Ollama MCP bridge
: "${OLLAMA_MODEL:=deepseek-r1:latest}"
export OLLAMA_MODEL
: "${PORT:=3100}"
export PORT
python3 /Users/visualval/.local/share/mcps/ollama-mcp/ollama_mcp_server.py
