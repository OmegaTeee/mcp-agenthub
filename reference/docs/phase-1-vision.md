# Phase 1: Vision & Goals

> **Status**: Foundation (Phases 2-4 build on this)
> **Your Action**: Read, understand, don't build yet. This sets intent.
> **Timeframe**: 0 weeks (conceptual only)

---

## Purpose

A containerized AI Agent Hub that unifies AI tool access across desktop applications. One endpoint, multiple MCP servers, enhanced prompts.

**Plain English**: Instead of configuring MCP servers separately in Claude Desktop, VS Code, Raycast, and Obsidian, you configure them once in a central router, and all apps talk to that router. The router also enhances prompts using Ollama before they hit paid APIs or bigger models.

---

## Problem Statement

| Problem | Today | With Router |
|---------|-------|-------------|
| **Fragmented Config** | Each app (Claude, VS Code, Raycast) needs separate MCP setup | Single router config, all apps auto‑benefit |
| **Manual Prompts** | You hand‑craft prompts without systematic improvement | Ollama auto‑enhances prompts per app/client |
| **No Shared Context** | Knowledge gained in one app stays in that app | Memory server (Phase 3) shares context across sessions |
| **Setup Friction** | Adding a new MCP means updating every app's config file | Add MCP to router, restart once, all apps see it |

---

## Outcomes (Why Build This)

| Outcome | How | Benefit |
|---------|-----|---------|
| **Reduced Setup Time** | Single router config replaces per‑app MCP configuration | New MCP servers take 5 minutes instead of 20 |
| **Seamless Data Sharing** | Memory server enables cross‑session context persistence | Your Obsidian notes, VS Code work, and Claude sessions remember each other |
| **Improved Prompt Quality** | Ollama enhancement refines prompts before paid APIs | Better results from Claude/Copilot, fewer retries |
| **Accelerated Learning** | Documentation + Learning Loop workflows capture knowledge automatically | Auto‑generated docs for your projects, saved to Obsidian |

---

## Design Principles

### 1. Elegant Simplicity
- Minimal config surface (JSON files, not UI dashboards initially)
- Sensible defaults (llama3.2 for fast enhance, deepseek-r1 for reasoning)
- Explicit overrides only when needed

**Why**: You're not building a SaaS platform. Keep configs simple enough to edit by hand and understand at a glance.

### 2. Professional Stack
- FastAPI (async, production‑ready, no experimental deps)
- Docker Compose (reproducible, portable, easy to understand)
- Industry‑standard patterns (circuit breakers, health checks, JSON‑RPC)

**Why**: This is infrastructure you'll maintain and extend. Use proven tools, not bleeding‑edge experiments.

### 3. AI‑Native Design
- Structured for AI readers (Claude, Copilot, Ollama) to parse and extend
- Clear separation of concerns (router logic, enhancement logic, MCP adapters)
- Documented so you (or an AI) can reason about it a year from now

**Why**: You'll be asking Claude/Copilot to help extend this. Make it easy for them to understand.

---

## Non‑Goals (What This *Isn't*)

❌ **Not a general‑purpose API gateway** — Specific to MCP + Ollama desktop use cases

❌ **Not replacing Claude or Copilot** — Enhancing their capabilities via a local router

❌ **Not managing LLM inference** — Ollama handles that separately (you already run it)

❌ **Not a user management system** — No registration, login, profiles, or role‑based access control

❌ **Not exposed to the internet** — Runs on `localhost` for desktop apps only

> **If external access is needed later**: Use a simple API key header (`X-API-Key`), not a full auth system. Desktop clients are already authenticated by the OS.

---

## Target Clients

The router is designed for *you* to use from:

- **Claude Desktop** (macOS native app)
- **VS Code** + GitHub Copilot Pro (editor + sidebar)
- **Perplexity Pro** (Desktop & Comet modes)
- **Raycast** (macOS launcher with custom commands)
- **Obsidian** (note‑taking app with plugin/HTTP support)
- **ComfyUI** (AI image generation workflow tool)

Each of these can point to `localhost:9090` and start using MCP servers managed by the router.

---

## Success Criteria

You'll know Phase 1 vision is good when:

1. ✅ You understand why a central router beats per‑app config
2. ✅ You can describe the "enhancement pipeline" (prompt → Ollama → improved prompt) in 2 sentences
3. ✅ You can sketch how a new MCP server gets added (add to JSON, restart router, all apps see it)
4. ✅ You know what "circuit breaker" means in context (fallback if a service is down)

---

## Next Steps

- **Phase 2** (Architecture & MVP): Build the actual router + enhancement middleware
- **Phase 3** (Desktop Integration): Wire Claude, VS Code, Raycast, etc. to the router
- **Phase 4** (Dashboard): Add web UI to inspect health, activity, cache stats

Do not skip Phase 1. If this vision doesn't make sense, no amount of code will fix it.
