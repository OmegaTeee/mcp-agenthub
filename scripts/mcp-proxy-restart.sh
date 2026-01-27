#!/usr/bin/env bash
set -euo pipefail
LOG=/tmp/mcp-proxy.log
DEBUG=/tmp/mcp-proxy-restart.debug
exec > >(tee -a "${DEBUG}") 2>&1

echo "[restart] proxy-config: /Users/visualval/.local/share/mcps/proxy-config.json"

# Find running proxy pid (match exact path)
OLD_PID=$(pgrep -f "/Users/visualval/go/bin/mcp-proxy --config /Users/visualval/.local/share/mcps/proxy-config.json" || true)
if [[ -n "${OLD_PID}" ]]; then
  echo "[restart] Found existing mcp-proxy pid: ${OLD_PID} — killing"
  kill "${OLD_PID}" || true
  sleep 1
else
  echo "[restart] No running proxy matching exact command found; trying generic pgrep"
  OLD_PID=$(pgrep -f mcp-proxy || true)
  if [[ -n "${OLD_PID}" ]]; then
    echo "[restart] Found mcp-proxy pid(s): ${OLD_PID} — killing"
    kill "${OLD_PID}" || true
    sleep 1
  fi
fi

# Start the proxy with nohup and write to LOG
echo "[restart] Starting mcp-proxy..."
nohup /Users/visualval/go/bin/mcp-proxy -config /Users/visualval/.local/share/mcps/proxy-config.json > "${LOG}" 2>&1 &
NEW_PID=$!
echo "[restart] started mcp-proxy pid: ${NEW_PID}"
sleep 1

echo "--- ${LOG} (head) ---"
if [[ -f "${LOG}" ]]; then
  sed -n '1,200p' "${LOG}"
else
  echo "(no log file yet)"
fi

# Wait for listener
for i in {1..10}; do
  if lsof -iTCP:9090 -sTCP:LISTEN -Pn >/dev/null 2>&1; then
    echo "[restart] proxy listening on :9090"
    break
  fi
  echo "[restart] waiting for proxy to listen... (${i})"
  sleep 0.5
done

echo "--- Test: ollama-mcp listTools via proxy ---"
curl -sS -X POST http://localhost:9090/ollama-mcp/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"listTools","params":{},"id":1}' | jq '.' || cat -

echo "--- Test: llm-text list_llm_txt via proxy ---"
curl -sS -X POST http://localhost:9090/llm-text/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"callTool","params": { "name":"list_llm_txt", "arguments": {} },"id":1}' | jq '.' || cat -

echo "--- tail ${LOG} ---"
if [[ -f "${LOG}" ]]; then
  tail -n 200 "${LOG}"
fi

exit 0
