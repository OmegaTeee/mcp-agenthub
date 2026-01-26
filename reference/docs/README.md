# AI Agent Hub: Phase-By-Phase Breakdown

> **Complete Guide to Building Local-First Tool Orchestration**
> Last Updated: January 2026

---

## Quick Reference

| Phase | Name | Focus | Your Action | Timeframe |
|-------|------|-------|-------------|-----------|
| **1** | Vision & Goals | Understanding | Read + internalize | 0 weeks |
| **2** | AI Agent Hub Core | Building the MVP | Write code, test locally | 1–2 weeks |
| **3** | Desktop Integration | Making it useful | Wire up apps, build pipelines | 1 week |
| **4** | Dashboard | Optional visibility | Add monitoring UI | 1 week (optional) |

---

## How to Use These Documents

1. **Start with Phase 1** (`phase-1-vision.md`)
   - Read to understand *why* you're building this
   - Don't skip this even if it seems simple
   - If you don't buy the vision, the code won't help

2. **Build Phase 2** (`phase-2-core.md`)
   - This is the actual router + enhancement middleware
   - Get it working with Docker Compose
   - Test with one MCP server before moving on
   - Stop here if you want a minimal MVP

3. **Wire Phase 3** (`phase-3-integration.md`)
   - Connect Claude Desktop, VS Code, Raycast, etc. to the router
   - See real value (apps talking to the router, prompts being enhanced)
   - Build the documentation pipeline as a proof-of-concept
   - This is where the router becomes **useful**

4. **Add Phase 4 (Optional)** (`phase-4-dashboard.md`)
   - Pure observability layer
   - Nice for understanding system behavior
   - Not required for the router to work
   - Skip if you prefer CLI/logs

---

## Key Decisions Built Into This Spec

### Decision 1: In-Memory Cache in Phase 2 (No Qdrant Yet)

**Why**: Operational simplicity. You don't need database persistence for the first 1–3 months of use.

**When to upgrade**: When you have >10K cached prompts or need persistence across restarts (probably month 2–3).

**How to upgrade**: Swap `cache.py` with `cache_qdrant.py` (spec includes both). No other changes needed.

---

### Decision 2: FastAPI + Docker Compose (Not Kubernetes)

**Why**: Production-grade but simple. Perfect for single-developer local infrastructure.

**Complexity**: Medium. You need to understand:
- FastAPI basics (routing, middleware)
- Docker Compose (service orchestration)
- JSON-RPC (MCP protocol)

**Overengineering check**: No. This is the minimum viable infrastructure for the problem.

---

### Decision 3: Local-Only (No Auth, No Internet)

**Why**: You're running this on your macOS machine. The OS already provides authentication.

**If you later need external access**: Add `X-API-Key` header. Nothing more. Don't build a full auth system.

---

### Decision 4: Four MCP Servers in MVP (Not Infinite)

**Why**: You've got Context7, Desktop Commander, Sequential Thinking, and Memory in the original router-spec. That's enough to learn the pattern.

**If you need more**: Add them one at a time using the "Adding a Custom MCP Server" section in Phase 2.

---

## The Learning Arc

### What You'll Learn

**Phase 1**: System design thinking (constraints, non-goals, design principles)

**Phase 2**:
- HTTP routing and proxying (how requests flow through services)
- Middleware architecture (how to intercept and enhance requests)
- Circuit breakers (how to handle failures gracefully)
- Caching strategies (LRU, semantic similarity)
- Docker Compose (reproducible multi-service setups)

**Phase 3**:
- Tool orchestration (chaining MCP servers into workflows)
- Client configuration (how to wire desktop apps together)
- Pipelines (how to automate multi-step tasks)

**Phase 4**:
- Observability (how to monitor a system)
- Real-time UI updates (HTMX without complexity)

### What You Won't Learn

❌ Authentication / Authorization (not needed locally)
❌ Database design (Phase 2 doesn't use Qdrant)
❌ React / Vue / complex frontend frameworks (HTMX is intentionally simple)
❌ Kubernetes / multi-region deployment (not relevant for local tools)

---

## Avoiding Over-Engineering

**The spec includes safeguards to prevent scope creep:**

1. **Phase gates**: Each phase is a checkpoint. Only move forward if the previous phase works.
2. **MVP-first mindset**: Phase 2 is deliberately minimal. No learning loops, no memory server, no dashboard.
3. **Optional upgrades**: Qdrant, pipelines, dashboard are all marked as "add when needed, not upfront."
4. **Clear success criteria**: Each phase has concrete "you'll know it's done when..." checks.

**How to stay on track**:
- Build Phase 2 in a weekend or two
- Use it for a week
- Then decide: Do I need Phase 3? Phase 4?
- Add only what solves a real problem you've felt

---

## Typical Timeline

### Week 1–2: Phase 2 (MVP)
- Day 1–2: Set up FastAPI project, Docker Compose, basic routing
- Day 3–4: Build enhancement middleware, integrate Ollama
- Day 5–6: Add circuit breaker logic, caching
- Day 7+: Test with MCP servers, debug

**Deliverable**: A working router at `localhost:9090`

### Week 3: Phase 3 (Real Usage)
- Day 1: Wire Claude Desktop to router
- Day 2: Wire VS Code to router
- Day 3: Add documentation pipeline
- Day 4–5: Build Raycast + Obsidian integrations
- Day 6–7: Test end-to-end workflows

**Deliverable**: Apps talking to the router, one automated pipeline working

### Week 4: Phase 4 (Optional)
- Day 1–3: Build dashboard HTML + HTMX
- Day 4–5: Connect backend endpoints
- Day 6–7: Test, polish

**Deliverable**: Visual monitoring at `localhost:9090/dashboard`

### Month 2+: Real Usage & Refinement
- Use Phase 2 + 3 setup for a month
- Observe pain points and opportunities
- Add features based on *actual* needs, not speculation

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Trying to Build Everything at Once

"I'll build the router + dashboard + memory server + learning loops all in one go."

**Why it fails**: Too many unknowns, no feedback loop, easy to get stuck.

**Fix**: Commit to Phase 2 only. Ship it, use it, then decide.

---

### ❌ Mistake 2: Adding Qdrant Before You Need It

"I want a production-grade system from day one."

**Why it fails**: Operational overhead. Debugging is harder. You probably won't hit the limits for months.

**Fix**: Use in-memory cache. Upgrade to Qdrant when you feel the pain (high cache misses, router restarts losing state).

---

### ❌ Mistake 3: Premature Generalization

"I'll make the router work for any MCP server, any client, any configuration."

**Why it fails**: Abstraction bloat. Your code becomes harder to understand and extend.

**Fix**: Build for your specific setup (Claude Desktop, VS Code, Raycast, Obsidian). Generalize later if needed.

---

### ❌ Mistake 4: Skipping Phase 1

"I just want the code, not the philosophy."

**Why it fails**: You'll build the wrong thing. Without a clear vision, every feature seems important.

**Fix**: Read Phase 1. Even if it takes 30 minutes. It'll save you from wandering.

---

### ❌ Mistake 5: Treating Phase 4 as Essential

"I can't use the router without a dashboard."

**Why it fails**: You lose months to UI polish before proving the core works.

**Fix**: Phase 2 + 3 work without Phase 4. Add the dashboard only if you want it.

---

## File Structure (After All Phases)

```
agenthub/
├── router/
│   ├── main.py                  # FastAPI app
│   ├── models.py                # Pydantic models (JSONRPCRequest, etc.)
│   ├── circuit_breaker.py       # Circuit breaker logic
│   ├── cache.py                 # In-memory LRU cache
│   ├── cache_qdrant.py          # Qdrant vector cache (Phase 2.1)
│   ├── middleware/
│   │   ├── enhance.py           # Prompt enhancement middleware
│   │   └── logging.py           # Activity logging
│   ├── adapters/
│   │   └── stdio.py             # STDIO → HTTP bridge for MCP servers
│   ├── pipelines/
│   │   └── documentation.py     # Documentation generation pipeline
│   ├── stats.py                 # Cache + model usage stats
│   └── dashboard.py             # Dashboard endpoints
├── templates/
│   ├── dashboard.html           # Main dashboard page
│   └── partials/
│       ├── health.html
│       ├── stats.html
│       └── activity.html
├── configs/
│   ├── mcp-servers.json         # MCP server registry
│   ├── enhancement-rules.json   # Per-client enhancement config
│   └── settings.py              # App configuration
├── docker-compose.yml           # Service orchestration
├── Dockerfile                   # Router image
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Project metadata
└── README.md                    # User guide

docs/
├── phase-1-vision.md           # This project
├── phase-2-core.md
├── phase-3-integration.md
└── phase-4-dashboard.md
```

---

## When to Stop (And Why That's OK)

### Stop After Phase 1 If
- The vision doesn't resonate
- You don't have multiple desktop apps you want to unify
- You're happy with per-app MCP configuration

---

### Stop After Phase 2 If
- You just wanted to learn about routing + enhancement middleware
- You want to use the router headless (CLI only, no UI)
- You don't need to wire up desktop apps yet

---

### Stop After Phase 3 If
- You've got desktop apps connected and pipelines working
- You don't care about visual dashboards
- Logs and CLI health checks are enough

---

### Stop After Phase 4 If
- You want to ship the router as your final product
- Everything is monitored and visible
- You're happy with what you've built

**There is no "right" endpoint.** Ship what makes sense for your goals.

---

## Support Resources

### If You Get Stuck on Phase 2
- **FastAPI docs**: https://fastapi.tiangolo.com/
- **Docker Compose guide**: https://docs.docker.com/compose/
- **MCP spec**: https://modelcontextprotocol.io/
- **Ask Claude**: "I'm building a FastAPI service that proxies JSON-RPC requests to MCP servers running in Docker Compose..."

### If You Get Stuck on Phase 3
- **Claude Desktop config**: https://github.com/anthropics/anthropic-sdk-python/discussions
- **Raycast API**: https://raycast.com/developers
- **Obsidian HTTP**: https://github.com/Quorafind/Obsidian-Mcp

### If You Get Stuck on Phase 4
- **HTMX docs**: https://htmx.org/
- **Jinja2 templates**: https://jinja.palletsprojects.com/
- **FastAPI templates**: https://fastapi.tiangolo.com/advanced/templates/

---

## Success Looks Like

### After Phase 2
```bash
$ docker compose up -d
$ curl http://localhost:9090/health
{
  "status": "healthy",
  "services": [
    {"name": "router", "status": "healthy"},
    {"name": "ollama", "status": "healthy"},
    {"name": "context7", "status": "healthy"}
  ]
}
```

### After Phase 3
- Claude Desktop sends a message
- Router enhances it with Ollama
- Router forwards to Context7
- Result comes back
- All transparent to the user

### After Phase 4
- Dashboard shows all services green
- Cache hit rate is 85%+
- Recent activity shows real requests flowing through

---

## One Final Clarification

**This is not enterprise software. It's infrastructure for your desk.**

You don't need:
- User management
- Audit logs
- SLAs
- Horizontal scaling
- Multi-region deployment

You do need:
- Simple, understandable code
- Works offline on your Mac
- Clear error messages
- Easy to debug when things break
- Easy to extend when you get ideas

Build accordingly. That's why this spec is 4 phases, not 20.

---

## Next Action

1. Read `phase-1-vision.md`
2. If it makes sense, read `phase-2-core.md`
3. If Phase 2 looks doable, create a new directory and start coding
4. Don't read Phase 3 until Phase 2 works
5. Don't read Phase 4 until Phase 3 works

Good luck. You're building something cool.
