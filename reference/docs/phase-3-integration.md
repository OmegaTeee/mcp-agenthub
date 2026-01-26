# Phase 3: Desktop Integration

> **Status**: Extend Phase 2 with client support
> **Your Action**: Do this only after Phase 2 MVP is stable
> **Timeframe**: 1 week (assumes Phase 2 works)

---

## Overview

Once your router is running, point each desktop app to it. Instead of each app managing its own MCP servers, they all talk to `localhost:9090` and get transparent enhancement + orchestration.

**Key insight**: Apps don't need to know about the router's internals. They just send requests to port 9090, and the router handles:
- Figuring out which MCP server to call
- Enhancing prompts per client
- Caching results
- Falling back gracefully if services are down

---

## 3.1 Client Configurations

### Claude Desktop

File: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Option 1: Proxy Mode (Recommended for Phase 2)**

```json
{
  "mcpServers": {
    "agenthub": {
      "command": "curl",
      "args": ["-X", "POST", "http://localhost:9090/mcp"],
      "env": {}
    }
  }
}
```

**Why this works**: Claude sends MCP requests to curl, which forwards them to the router. Simple, no special config needed.

**Option 2: Direct HTTP (Phase 3+, if you implement SSE)**

If you implement SSE (Server-Sent Events) endpoint in the router:

```json
{
  "mcpServers": {
    "agenthub": {
      "url": "http://localhost:9090/sse",
      "transport": "sse"
    }
  }
}
```

**For now, stick with Option 1.**

### VS Code

File: `.vscode/mcp.json` (create in project root)

```json
{
  "mcp.servers": {
    "agenthub": {
      "type": "http",
      "url": "http://localhost:9090",
      "headers": {
        "X-Client-Name": "vscode"
      }
    }
  }
}
```

**What this does**: VS Code will send all MCP requests to the router with a header that says "I'm VS Code." The router reads this header and applies VS Code-specific enhancement rules (e.g., use qwen2.5-coder model for code suggestions).

### Raycast

File: `~/.config/raycast/scripts/mcp-query.sh` (create custom Raycast script)

```bash
#!/bin/bash

# Raycast metadata
# @raycast.schemaVersion 1
# @raycast.title MCP Query
# @raycast.mode fullOutput
# @raycast.argument1 { "type": "text", "placeholder": "Query" }

curl -s -X POST http://localhost:9090/mcp/sequential-thinking/tools/call \
  -H "Content-Type: application/json" \
  -H "X-Client-Name: raycast" \
  -d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"params\": {
      \"name\": \"think\",
      \"arguments\": { \"query\": \"$1\" }
    },
    \"id\": 1
  }"
```

**What this does**: When you type "MCP Query" in Raycast, it sends your query to the router's sequential-thinking server. The router enhances it with llama3.2 (fast) and returns structured reasoning.

### Obsidian

**Option 1: Native HTTP + Plugin**

Install [Obsidian MCP plugin](https://obsidian.md/plugins?id=mcp) and configure:

```json
{
  "mcp_endpoint": "http://localhost:9090",
  "client_name": "obsidian",
  "default_vault_path": "~/Obsidian",
  "auto_link": true
}
```

**Option 2: External Fetch Script**

Or use a custom Obsidian script that calls the router:

```javascript
// In Obsidian Script Editor or QuickAdd
const response = await fetch("http://localhost:9090/ollama/enhance", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Client-Name": "obsidian"
  },
  body: JSON.stringify({
    prompt: "Your note content or query"
  })
});

const enhanced = await response.json();
// Now insert enhanced text into note
```

---

## 3.2 Documentation Pipeline

### Purpose

Automatically generate documentation from your codebases and save it to Obsidian. Triggered manually or via Raycast.

### How It Works (End-to-End)

**Trigger**: You run a Raycast command or call an API endpoint

**Flow**:
1. **Pack Repository** — Compress a codebase (e.g., with Repomix) to a token-efficient format
2. **Enhance** — Send to Ollama (deepseek-r1) with system prompt: "Document this codebase for beginners"
3. **Structure** — Run through Sequential Thinking to organize into logical sections
4. **Write to Obsidian** — Use Desktop Commander to write `.md` file to your vault

**Result**: A well-structured, auto-generated doc file appears in `~/Obsidian/Projects/{project_name}.md`

### Implementation (Simplified)

```python
# router/pipelines/documentation.py

from router.models import JSONRPCRequest
from datetime import datetime

async def documentation_pipeline(
    repo_path: str,
    project_name: str,
    vault_path: str = "~/Obsidian/Projects"
) -> dict:
    """Generate documentation from codebase → Obsidian."""

    # Step 1: Create documentation prompt
    doc_prompt = f"""
    Generate technical documentation for: {repo_path}

    Include:
    - Architecture overview (max 500 words)
    - Setup instructions with exact commands
    - Key components and their responsibilities
    - Common workflows
    """

    # Step 2: Enhance with deepseek-r1 (reasoning + quality)
    enhanced = await enhance_prompt(
        prompt=doc_prompt,
        client="documentation-pipeline",
        model="deepseek-r1:14b",
        system="""You are a technical documentation specialist.
                  Format in Markdown with clear headers.
                  Include code blocks for commands.
                  Use [[wikilinks]] for cross-references."""
    )

    # Step 3: Structure with Sequential Thinking
    structure_request = JSONRPCRequest(
        method="tools/call",
        params={
            "name": "sequential_thinking",
            "arguments": {
                "thought": enhanced,
                "thought_number": 1,
                "total_thoughts": 3
            }
        }
    )
    structured = await route_to_server("sequential-thinking", structure_request)

    # Step 4: Write to Obsidian vault
    output_path = f"{vault_path}/{project_name}.md"

    doc_content = f"""---
tags: [project, documentation, auto-generated]
created: {datetime.now().isoformat()}
source: {repo_path}
---

# {project_name}

{structured['result']}

---
*Generated by AI Agent Hub Documentation Pipeline*
"""

    # Step 5: Use Desktop Commander to write file
    write_request = JSONRPCRequest(
        method="tools/call",
        params={
            "name": "write_file",
            "arguments": {
                "path": output_path,
                "content": doc_content
            }
        }
    )
    await route_to_server("desktop-commander", write_request)

    return {
        "status": "complete",
        "output_path": output_path,
        "obsidian_url": f"obsidian://open?vault=Obsidian&file=Projects/{project_name}"
    }
```

### Router Endpoint

```python
@app.post("/pipelines/documentation")
async def run_documentation_pipeline(
    repo_path: str,
    project_name: str,
    vault_path: str = "~/Obsidian/Projects"
) -> dict:
    return await documentation_pipeline(repo_path, project_name, vault_path)
```

### Triggering It

**From Raycast**:
```bash
curl -X POST http://localhost:9090/pipelines/documentation \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/my-project",
    "project_name": "My Project"
  }'
```

**From VS Code Command Palette**:
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "MCP: Document Workspace",
      "type": "shell",
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://localhost:9090/pipelines/documentation",
        "-H", "Content-Type: application/json",
        "-d", "{\"repo_path\": \"${workspaceFolder}\", \"project_name\": \"${workspaceFolderBasename}\"}"
      ]
    }
  ]
}
```

---

## 3.3 Learning Loop (Optional Phase 3 Extension)

### Concept

After a session, automatically capture what you learned:

1. Extract key facts from your conversation
2. Check if similar facts already exist in memory
3. If new, add to Obsidian + Memory Server with embeddings
4. If duplicate, note it for later deduplication

### Why It Matters

Over time, your router becomes a **knowledge capture system**, not just a tool proxy. Every interaction with Claude, VS Code, or Raycast contributes to your personal knowledge base.

### Simple Implementation (Non-MVP)

```python
@app.post("/learning/capture")
async def capture_learning(
    topic: str,
    facts: list[str],
    source_app: str
) -> dict:
    """Capture learning from a session."""
    
    # Embed facts
    embeddings = await ollama_embed(facts, model="nomic-embed-text")
    
    # Check for duplicates in memory
    duplicates = await check_memory_for_similar(embeddings)
    
    # Store new facts
    new_facts = [f for f in facts if f not in duplicates]
    
    # Write to Obsidian if new
    if new_facts:
        await write_learning_note(topic, new_facts, source_app)
    
    return {
        "new": len(new_facts),
        "duplicates": len(duplicates),
        "note_path": f"Learning/{topic}.md"
    }
```

**Skip in MVP**. Build this after Phase 2 + 3 are solid.

---

## Success Criteria for Phase 3

You'll know Phase 3 is done when:

1. ✅ Claude Desktop connects to router and can call tools via the router
2. ✅ VS Code enhancement uses qwen2.5-coder model (test with code prompts)
3. ✅ Raycast "MCP Query" command returns structured reasoning
4. ✅ Obsidian integration works (optional, but nice to have)
5. ✅ Documentation pipeline generates a full doc and writes to Obsidian vault
6. ✅ Each app's enhancement rules work as expected (different models per client)

---

## Phase 3 Deliverables

- Client configs for Claude, VS Code, Raycast, Obsidian
- Documentation pipeline endpoint (`/pipelines/documentation`)
- Raycast scripts / VS Code tasks for quick triggers
- Test docs in Obsidian vault
- Updated README with client setup instructions

---

## Clarification: Why Separate Documentation as a Pipeline?

**Reason 1**: It's optional. Phase 2 works fine without it.

**Reason 2**: It demonstrates how to chain multiple MCP servers (enhancement → sequential thinking → desktop commander) into a useful workflow. You can extend this pattern to other automations.

**Reason 3**: It forces you to write code that orchestrates tools, which is the core learning goal.

**Decision**: Phase 3 includes client integrations (essential) + documentation pipeline as a proof-of-concept for chaining tools. Build one, understand the pattern, add others as needed.

---

## Next Steps

1. **Phase 2 must be stable first** — Don't start Phase 3 until Phase 2 works
2. **Start with one client** — Configure Claude Desktop first, test it, then add VS Code
3. **Test each enhancement model** — Make sure llama3.2, deepseek-r1, qwen2.5 behave as expected
4. **Add documentation pipeline** as a capstone (shows you can orchestrate multiple tools)
5. **Decide on Phase 4** — Does a dashboard matter? Only if you want observability.

Phase 3 is where the router becomes truly useful. Phase 2 is infrastructure. Phase 3 is where you actually use it.
