# Phase 2: AI Agent Hub Core (MVP)

> **Status**: Implementation starts here
> **Your Action**: Build this first, get it working, then decide if you need Phases 3–4
> **Timeframe**: 1–2 weeks (solo dev, not rushing)

---

## Overview

**Goal**: A simple FastAPI service that acts as an HTTP proxy to MCP servers and enhances prompts via Ollama.

**Architecture in 3 layers**:

```
┌─────────────────────────────────────────────────────┐
│ Desktop Apps (Claude, VS Code, Raycast, Obsidian)   │
│ All talk to http://localhost:9090                   │
└────────────────┬────────────────────────────────────┘
                 │ HTTP
                 ▼
┌─────────────────────────────────────────────────────┐
│ AI Agent Hub (FastAPI)                                │
│ ┌──────────────────┐  ┌──────────────────────────┐ │
│ │ Proxy Layer      │→ │ Enhancement Middleware   │ │
│ │ (forward to MCP) │  │ (calls Ollama)           │ │
│ └──────────────────┘  └──────────────────────────┘ │
└────────────────┬───────────────┬────────────────────┘
                 │               │
         HTTP    │               │ HTTP
                 ▼               ▼
         ┌──────────────┐  ┌──────────────┐
         │ MCP Servers  │  │ Ollama       │
         │ (in Docker)  │  │ (native Mac) │
         └──────────────┘  └──────────────┘
```

**What it does**:
1. Client sends: `POST http://localhost:9090/mcp/context7/tools/call` with a JSON-RPC request
2. Router looks up "context7" in config and forwards the request
3. Optional: Enhancement middleware intercepts and asks Ollama to improve the prompt
4. Response comes back to the client
5. If a server is down, circuit breaker returns a fallback instead of hanging

**What it doesn't do (yet)**:
- No memory/knowledge graph (Phase 3)
- No dashboard (Phase 4)
- No learning loops
- Just routing + caching + enhancement

---

## 3.1 Router Service (The Core)

### Endpoints

**Health checks** (for you to monitor):
```
GET  /health              → All servers' status in one call
GET  /health/{server}     → Single server status (e.g., /health/context7)
```

**The main proxy** (what clients call):
```
POST /mcp/{server}/{path} → Forward JSON-RPC to an MCP server
                             (e.g., POST /mcp/context7/tools/call)
```

**Optional direct enhancement** (for testing):
```
POST /ollama/enhance      → Ask Ollama to improve a prompt
```

### Server Registry

File: `configs/mcp-servers.json`

```json
{
  "servers": {
    "context7": {
      "url": "http://context7:3001",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "desktop-commander": {
      "url": "http://desktop-commander:3002",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "sequential-thinking": {
      "url": "http://sequential-thinking:3003",
      "transport": "http",
      "health_endpoint": "/health"
    },
    "memory": {
      "url": "http://memory:3004",
      "transport": "http",
      "health_endpoint": "/health"
    }
  }
}
```

**What this means**:
- `url`: Where the MCP server lives (inside Docker)
- `transport`: How it communicates (`http` or `stdio`)
- `health_endpoint`: How to check if it's alive

---

## 3.2 Enhancement Middleware

### How It Works (Plain English)

1. A client sends a request to the router
2. Router checks: "Is this request from Claude? VS Code? Raycast?"
3. Based on the client, router picks an Ollama model and system prompt
4. Router asks Ollama: "Here's a prompt. Improve it for clarity/structure/code/etc."
5. Ollama returns an improved prompt
6. Router forwards the improved prompt to the actual MCP server
7. Response comes back

### Enhancement Rules

File: `configs/enhancement-rules.json`

```json
{
  "default": {
    "enabled": true,
    "model": "llama3.2:3b",
    "system_prompt": "Improve clarity and structure. Preserve intent. Return only the enhanced prompt."
  },
  "clients": {
    "claude-desktop": {
      "model": "deepseek-r1:14b",
      "system_prompt": "Provide structured responses with clear reasoning. Use Markdown."
    },
    "vscode": {
      "model": "qwen2.5-coder:7b",
      "system_prompt": "Code-first responses. Include file paths. Minimal prose."
    },
    "raycast": {
      "model": "llama3.2:3b",
      "system_prompt": "Action-oriented. Suggest CLI commands. Under 200 words."
    },
    "obsidian": {
      "model": "llama3.2:3b",
      "system_prompt": "Format in Markdown. Use [[wikilinks]] and #tags."
    }
  },
  "fallback_chain": ["phi3:mini", null]
}
```

### Model Selection Rationale

| Model | Purpose | Trade-off | When |
|-------|---------|-----------|------|
| `llama3.2:3b` | Fast, light enhancement | Less accuracy | Raycast, Obsidian (fast response matters) |
| `deepseek-r1:14b` | Complex reasoning | Slower (1-2s) | Claude Desktop (user can wait for quality) |
| `qwen2.5-coder:7b` | Code generation | Specialized | VS Code (code-tuned model helps) |
| `phi3:mini` | Fallback (runs on any Mac) | Basic quality | If preferred model OOM or timeout |

### Prompt Cache (Two‑Tier Strategy)

**Why caching?** Avoid re‑processing identical or similar prompts. Saves inference time and Ollama load.

**L1 Cache (Exact Match)**:
- Key: Hash of the exact prompt text
- Result: Cached enhanced prompt
- Speed: Instant (<1ms)
- Use case: User runs the same command twice

**L2 Cache (Semantic Similarity)**:
- Key: Embedding of the prompt (using `nomic-embed-text`)
- Match: If embedding similarity > 0.85 (cosine distance)
- Speed: Sub-millisecond with proper indexing
- Use case: "Explain Docker" and "What is Docker?" are similar enough

**LRU Eviction**: When cache fills to 1000 prompts, discard oldest unused ones.

**Plain English**: The cache is like a "frequently asked questions" board. If someone asks the exact same question, you answer from memory instantly. If they ask something *very similar*, you also answer from memory. When the board gets full, you erase the oldest notes that nobody reads anymore.

### Important: Start Without Qdrant

In Phase 2 MVP, keep the cache **in-memory** (Python dict with LRU logic). It's fast enough for dev/personal use and requires zero config.

**When to upgrade to Qdrant** (Phase 2.1):
- Cache persists across router restarts ✓
- You're building a corpus of 5,000+ enhanced prompts
- You want to introspect cache stats via a dashboard

See **Section 3.2.1** in the full spec if you need Qdrant later. Don't add it in MVP.

---

## 3.3 Circuit Breaker & Graceful Fallback

**What is a circuit breaker?**

Imagine your desktop-commander MCP server crashes. Without a circuit breaker, the router would try to talk to it, timeout, try again, timeout again — total slowdown. **With** a circuit breaker, the router notices "desktop-commander has failed 3 times in a row" and **stops trying** for 30 seconds. After 30 seconds, it tests once. If it's back, great. If not, it waits another 30 seconds.

**Three states**:

| State | What It Means | Router Behavior |
|-------|---------------|-----------------|
| **CLOSED** | Service is healthy | Forward requests normally |
| **OPEN** | Service is broken | Reject requests, return fallback |
| **HALF_OPEN** | Testing recovery | Allow one test request, see what happens |

**Fallback Strategy**:

| Scenario | Fallback |
|----------|----------|
| Ollama down | Return original prompt (unenhanced) |
| MCP server down | Return clear error + retry hint |
| Timeout | Return partial response if available |
| Model context exceeded | Use smaller model or skip enhancement |

**Plain English**: If Ollama crashes, your enhanced prompts aren't critical — users still get their original prompts. If a tool like desktop-commander crashes, you don't hang forever; you tell the user "it's down, try again in 30s."

---

## 3.4 MCP Server Containers

### Docker Compose Setup

File: `docker-compose.yml` (in project root)

```yaml
version: "3.9"

services:
  router:
    build: .
    ports:
      - "9090:9090"
    environment:
      - OLLAMA_HOST=host.docker.internal
      - OLLAMA_PORT=11434
    volumes:
      - ./configs:/app/configs:ro
    depends_on:
      - context7
      - desktop-commander
      - sequential-thinking
      - memory

  context7:
    image: node:20-slim
    working_dir: /app
    command: ["node", "node_modules/@upstash/context7-mcp/dist/index.js"]
    volumes:
      - ./node_modules:/app/node_modules:ro
    expose:
      - "3001"

  desktop-commander:
    image: node:20-slim
    working_dir: /app
    command: ["node", "node_modules/@wonderwhy-er/desktop-commander/dist/index.js"]
    volumes:
      - ./node_modules:/app/node_modules:ro
      - ${HOME}:/host-home:rw
    expose:
      - "3002"

  sequential-thinking:
    image: node:20-slim
    working_dir: /app
    command: ["node", "node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js"]
    volumes:
      - ./node_modules:/app/node_modules:ro
    expose:
      - "3003"

  memory:
    image: node:20-slim
    working_dir: /app
    command: ["node", "node_modules/@modelcontextprotocol/server-memory/dist/index.js"]
    volumes:
      - ./node_modules:/app/node_modules:ro
    expose:
      - "3004"
```

### Adding a Custom MCP Server (Later)

When you want to add your own MCP server:

1. **Pick a port**: 3001–3010 are reserved. Use 3011, 3012, etc. for custom servers.
2. **Add to docker-compose.yml**:
   ```yaml
   my-custom-server:
     image: node:20-slim
     command: ["node", "path/to/server.js"]
     volumes:
       - ./node_modules:/app/node_modules:ro
     expose:
       - "3011"
   ```
3. **Register in mcp-servers.json**:
   ```json
   "my-custom": {
     "url": "http://my-custom-server:3011",
     "transport": "http",
     "health_endpoint": "/health"
   }
   ```
4. **Restart**: `docker compose up -d`
5. **Verify**: `curl http://localhost:9090/health | jq '.circuit_breakers'`

---

## Getting Phase 2 Running

### Prerequisites

- macOS with Ollama already running (native app, `localhost:11434`)
- Colima or Docker Desktop for containerization
- Python 3.11+
- Node 20+ (for MCP servers)

### Initial Setup

```bash
# Clone or init your project
git init agenthub
cd agenthub

# Create directories
mkdir -p router configs

# Copy configs from spec
cat > configs/mcp-servers.json << 'EOF'
{ "servers": { ... } }
EOF

cat > configs/enhancement-rules.json << 'EOF'
{ "default": { ... } }
EOF

# Install Python deps
pip install fastapi uvicorn httpx pydantic

# Build router
docker compose build

# Start all services
docker compose up -d

# Verify health
curl http://localhost:9090/health
```

### Testing a Call

```bash
# Test enhancement endpoint
curl -X POST http://localhost:9090/ollama/enhance \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: raycast" \
  -d '{"prompt": "explain docker"}'

# Test MCP proxy (if context7 is up)
curl -X POST http://localhost:9090/mcp/context7/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {"name": "lookup", "arguments": {"query": "how to use docker"}},
    "id": 1
  }'
```

---

## Success Criteria for Phase 2

You'll know MVP is done when:

1. ✅ Router starts with `docker compose up -d`
2. ✅ `curl http://localhost:9090/health` shows all services healthy
3. ✅ Prompt enhancement works: `curl .../ollama/enhance` returns an improved prompt
4. ✅ One MCP server proxies correctly (e.g., context7 can be called via the router)
5. ✅ Circuit breaker activates when you manually stop a service
6. ✅ Router recovers gracefully when service restarts
7. ✅ Config files (mcp-servers.json, enhancement-rules.json) are editable, and changes work after restart

---

## Phase 2 Deliverables

- `router/main.py` — FastAPI app with health, proxy, and enhancement endpoints
- `router/circuit_breaker.py` — Circuit breaker logic
- `router/middleware/enhance.py` — Enhancement middleware with Ollama integration
- `router/cache.py` — In-memory prompt cache with LRU
- `docker-compose.yml` — All services (router + MCP servers)
- `configs/mcp-servers.json` — Server registry
- `configs/enhancement-rules.json` — Per-client enhancement rules
- `Dockerfile` — Build router image
- `README.md` — How to run and test

---

## Clarification: Why Not Start With Qdrant?

**Reason 1**: Qdrant adds operational complexity (another service, volumes, migrations).

**Reason 2**: In-memory cache is 99% good enough for personal use. You're enhancing maybe 50–200 prompts per day, not millions.

**Reason 3**: If you later realize you need persistence (e.g., router restarts lose cache), adding Qdrant is a clean upgrade (Section 3.2.1 in full spec). No refactoring required.

**Decision**: Start with in-memory LRU cache. If you hit >10K cached prompts or need persistence across restarts, upgrade to Qdrant. Expected timeframe: 2–3 months of regular use.

---

## Next Steps

1. **Read Phase 1** if you haven't (to understand *why*)
2. **Build Phase 2** (this is the core)
3. **Test Phase 2** with Claude Desktop or VS Code
4. **Evaluate Phase 3/4** once Phase 2 is stable (week 2–3)

Do not add Phase 3 features (memory, pipelines) until Phase 2 is solid. A working MVP beats a theoretical full system.
