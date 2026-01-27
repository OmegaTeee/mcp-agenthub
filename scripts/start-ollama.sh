#!/usr/bin/env bash
# change to the ollama-mcp directory so module imports resolve
cd "${HOME}/.local/share/mcps/ollama-mcp" || exit 1
# Start minimal ollama bridge (uses stdlib HTTPServer to avoid FastAPI/pydantic issues)
~/.local/share/mcps/ollama-mcp/venv/bin/python ~/.local/share/mcps/ollama-mcp/minimal_ollama_mcp_server.py > /tmp/ollama-mcp.log 2>&1 &
echo "started ollama-mcp, logs: /tmp/ollama-mcp.log"
