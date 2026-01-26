# AI Agent Hub: User & Agent Specifications

> **For Non-Programmers, End-Users, and AI Agents**
> What this system does, how to use it, what to expect

---

## Plain English: What Is This?

A **central hub** on your Mac that connects all your AI tools (Claude, Copilot, Raycast, Obsidian) to specialized helper programs, and automatically improves your prompts before sending them to AI models.

**Simple analogy**: Like a receptionist who:
1. Receives requests from multiple people (your apps)
2. Makes smart suggestions to improve the request
3. Routes it to the right specialist (tool/MCP server)
4. Returns the result

---

## What You Get (Capabilities)

### ✅ One Place to Configure Everything

**Without router:**
- Configure Context7 in Claude Desktop
- Configure Context7 again in VS Code
- Configure Context7 again in Raycast
- (Repeat 10+ times for different tools)

**With router:**
- Configure Context7 once in the router
- All apps automatically see it
- Add a new tool? All apps benefit instantly

**Result**: Setup time drops from 2 hours to 30 minutes.

---

### ✅ Automatic Prompt Improvement

**Without router:**
- You type: "explain docker"
- Claude gets: exactly what you typed
- Often need to rephrase or retry

**With router:**
- You type: "explain docker"
- Router thinks: "This is for VS Code, so I should make it code-focused"
- Router improves it to: "Explain Docker with practical examples for developers. Include CLI commands and Dockerfile usage."
- Claude gets: better prompt → better answer

**Result**: Better answers, fewer retries, less frustration.

---

### ✅ Seamless Access to Tools

The router gives you access to these capabilities without managing them individually:

| Tool | What It Does | When You'd Use It |
|------|--------------|------------------|
| **Context7** | Fetch documentation from libraries (React, Node.js, Python, etc.) | "How do I use React hooks?" — automatically gets real React docs |
| **Desktop Commander** | File operations, terminal commands, process management | "List files in my Documents folder" or "Kill that stuck process" |
| **Sequential Thinking** | Step-by-step reasoning and planning | "Break down this complex problem into steps" |
| **Memory Server** | Remember facts across multiple conversations | "Remember that I prefer async/await over promises" — stays remembered |
| **DeepSeek Reasoner** | Local reasoning without hitting Claude API | Complex planning tasks, run locally for privacy |

---

### ✅ Shared Memory (Context Between Sessions)

**Without router:**
- Tell Claude: "I prefer async/await over promises"
- Start a new conversation with Claude
- Tell Claude again: "I prefer async/await over promises"
- (Memory is lost between sessions)

**With router + Memory Server:**
- Tell Claude: "I prefer async/await over promises"
- Router stores this fact with embeddings (semantic search-friendly)
- Start 5 new conversations → All remember your preference
- Switch to Obsidian, VS Code, or Raycast → They all know too

**Result**: No more repeating yourself.

---

### ✅ Cost & Privacy Benefits

**Using Direct APIs:**
- Every request to Claude costs money
- Every request sends your data to Anthropic's servers
- Running DeepSeek R1 locally? Still need Claude for other tasks

**Using Router + Local Models:**
- Prompt enhancement runs locally (free, instant, private)
- Complex reasoning via DeepSeek R1 runs locally (free, no API costs)
- Only send to Claude when necessary (save money + privacy)
- Many tasks never need Claude at all

**Result**: Estimated 40-60% reduction in API costs.

---

## How It Works (Without Code)

### The Flow

```
You type in Claude Desktop
       ↓
Router receives it
       ↓
Router thinks: "This came from Claude Desktop"
       ↓
Router checks: "Should I improve this? Based on Claude Desktop's rules... yes."
       ↓
Router sends to Ollama (local AI)
       ↓
Ollama improves the prompt
       ↓
Router caches the improvement (so next similar prompt is instant)
       ↓
Router forwards improved prompt to your tool (Context7, Desktop Commander, etc.)
       ↓
Tool returns result
       ↓
You see answer in Claude Desktop
```

**Key point**: All of this happens transparently. You don't see it. Just better answers.

---

## What Happens When You Start Using It

### Day 1 (Setup Complete)
- All your apps point to `localhost:9090` (the router)
- Router is running in the background
- Everything works like before, but...

### Week 1
- You notice answers are slightly better formatted
- Context7 is automatically available everywhere
- You try Desktop Commander and it works instantly

### Week 2–3
- You realize you're not repeating context anymore (Memory is working)
- You start chaining commands (ask for a file, router modifies it, saves it back)
- Obsidian, VS Code, Claude all "know" each other now

### Month 2+
- You build a workflow: "Generate documentation → Save to Obsidian → Index it → Make it searchable"
- Realizes this happens without manual steps
- Uses local models for reasoning (saves money vs Claude API)

---

## What You Can Ask For (Example Prompts)

### With Router + Context7
- "Use context7: How do I implement useEffect in React?"
- "Use context7: What's the Python datetime module?"
- → Automatically gets real docs

### With Router + Desktop Commander
- "List all files in ~/Documents modified in the last week"
- "Kill the process using port 8000"
- "Find all .env files on my system"

### With Router + Sequential Thinking
- "Break down building a web scraper into 5 steps"
- "Plan a migration from MongoDB to PostgreSQL"
- "What's the best architecture for a microservices system?"

### With Router + Memory Server
- "Remember: I always use TypeScript, never JavaScript"
- (Next time, Claude/Copilot know this)
- "What did I say I prefer for testing? [You don't have to repeat it]"

### With Router + DeepSeek Reasoner (No API Cost)
- "Do complex reasoning locally" (free, instant)
- "Plan a system design locally" (free, no API call)
- Good for: offline work, privacy-sensitive tasks, budget constraints

---

## What You Need to Use It

### Hardware
- Your Mac (M1/M2/M3 preferred, works on Intel)
- About 8GB available RAM
- 20GB disk space for models

### Software
- Ollama running (already installed? Yes)
- Docker Desktop or Colima (container runtime)
- The router (someone builds this from the spec)

### Apps
- Claude Desktop (or VS Code, Raycast, Obsidian — any combination)
- At least one MCP server (included with router)

### Skills Required
- None. Setup is clicking buttons and copying config.
- No programming knowledge needed.

---

## How Fast Is It?

| Operation | Time | Why |
|-----------|------|-----|
| First prompt enhancement | 0.5–1.5 seconds | Ollama loads model first time |
| Cached prompt (L1) | <1ms | Already computed, just lookup |
| Cached prompt (L2 semantic) | <50ms | Vector search for "similar" prompts |
| Routing to MCP server | 50–200ms | Network roundtrip in Docker |
| Context7 doc fetch | 1–3 seconds | Library docs downloaded and parsed |
| Total first-time flow | ~3–5 seconds | Worth it for better answer |

**In practice**: You don't notice it. Feels instant.

---

## Privacy & Security Guarantees

### Local-Only
- Router runs on your Mac only (localhost:9090)
- All models run locally (Ollama, DeepSeek R1)
- Prompt improvement happens locally
- Your data never leaves your machine unless you explicitly send to Claude

### Exception: When You Use Paid APIs
- Context7: Queries Upstash (library docs) — public data only
- Claude: Sends to Anthropic — your choice to use
- Obsidian: Stays local unless you sync vault
- Desktop Commander: Local only (just file ops)

### Exception: You Can Override
- All local-only by default
- If you want to send logs somewhere, you can (optional)
- If you want cloud backup of memory, you can (optional)
- But out-of-box? Everything is private

---

## What Happens If Something Breaks

### Service Down: No Crash, No Loss

| If This Fails | What Happens |
|---------------|--------------|
| Ollama crashes | Prompts sent as-is, unenhanced (still works, just less polished) |
| Context7 down | You can't use context7, but other tools work fine |
| Router crashes | Restart it (takes 10 seconds) |
| Memory forgets something | Feature failed gracefully, you just repeat yourself once |

**Philosophy**: Always degraded, never broken.

---

## Customization (Without Programming)

### What You Can Control (Config Files)

1. **Which models to use per app**
   - Claude Desktop uses better (slower) model
   - Raycast uses faster (lighter) model
   - VS Code uses code-specific model

2. **When enhancement happens**
   - Always enhance? Or only for certain apps?
   - Always enhance? Or only for certain types of prompts?

3. **Which tools are available**
   - Turn off Context7 if you don't need it
   - Turn on DeepSeek Reasoner for complex tasks
   - Add new tools as they come out

4. **How long to cache**
   - Cache for 1 day? 1 week? Forever?
   - What's the cache size limit?

**Note**: All changes are JSON config files. No programming, just editing text.

---

## What's NOT Included (Limits)

❌ **Not**: A new AI model
- Router uses Claude, Copilot, DeepSeek, etc. (you provide those)
- Router just routes and improves, doesn't replace them

❌ **Not**: A database or file storage
- Router doesn't store your files
- It caches prompts (temporary) and memory (optional)
- Your files stay where they are (Obsidian, Desktop, etc.)

❌ **Not**: A web app or SaaS
- No server to log into
- No account system
- No monthly fee
- Just software that runs on your Mac

❌ **Not**: Replacement for Claude/Copilot
- You still need Claude Desktop or VS Code Copilot
- Router enhances them, doesn't replace them

---

## Example Scenarios

### Scenario 1: You're a Writer

**Without Router:**
```
Me: "How do I structure a blog post about AI?"
Claude: [Generic answer]
Me: "That's not technical enough"
Claude: [Revise]
Me: [Manually configure Context7 in Claude]
Me: "Now add React documentation examples"
Claude: [Works, but took time]
```

**With Router:**
```
Me: "How do I structure a blog post about AI?"
Router: [Improves for clarity]
Claude: [Better structured answer]
Me: "Add React documentation"
Router: [Fetches via Context7]
Claude: [Immediate, with real docs]
```

**Benefit**: No manual config, better answers, less back-and-forth.

---

### Scenario 2: You're a Developer

**Without Router:**
```
Me: "How do I implement this in TypeScript?"
Claude: [Generic answer]
Me: [Manually run code through desktop commander]
Me: [Paste result back to Claude]
Me: [Ask again if wrong]
```

**With Router:**
```
Me: "How do I implement this in TypeScript?"
Router: [Improves for code-focused context]
Claude: [Code-specific answer]
Router: [Automatically runs via Desktop Commander if needed]
Claude: [Result with actual file output]
```

**Benefit**: Workflow is seamless, code and conversation flow together.

---

### Scenario 3: You Use Multiple Apps

**Without Router:**
```
Me in Claude: "How does React useEffect work?"
[Configure Context7]
Me in VS Code: "Wait, how does useEffect work?"
[Configure Context7 again]
Me in Obsidian: "Taking notes on useEffect"
[No context7 available]
```

**With Router:**
```
Me in Claude: "How does useEffect work?"
Router: [Fetches React docs via Context7]
Claude: [Real docs]

Me in VS Code: "How does useEffect work?"
Router: [Same docs, already cached]
VS Code: [Instant answer]

Me in Obsidian: "Taking notes on useEffect"
Router: [Remembers previous context]
Obsidian: [Smart suggestions based on prior discussion]
```

**Benefit**: Consistency across all tools, no repeated setup.

---

## Success Metrics (How to Know It's Working)

### Week 1
- ✅ All apps connect to router without errors
- ✅ Prompts come back formatted better than before
- ✅ No slowdown compared to direct API calls

### Week 2–3
- ✅ You notice Context7 docs auto-fetching
- ✅ Memory server remembers your preferences
- ✅ No time spent on manual tool configuration

### Month 1+
- ✅ You're running complex reasoning locally (saving money)
- ✅ You're chaining multiple tools in workflows
- ✅ You can't imagine going back to managing each app separately

---

## Getting Started (Non-Programmer Path)

1. **Have someone build Phase 2 of the spec**
   - Estimated time: 1–2 weeks
   - Deliverable: Router running at localhost:9090

2. **Copy the provided config files to your apps**
   - Claude Desktop: Paste config
   - VS Code: Paste config
   - Raycast: Paste config
   - (No programming, just copy-paste)

3. **Start using your apps**
   - Everything works like before
   - But quietly better behind the scenes

4. **Explore gradually**
   - Week 1: Just use it, enjoy better answers
   - Week 2: Try Context7 with a prompt
   - Week 3: Check if Memory remembered something
   - Month 2: Build a simple workflow

---

## FAQ

**Q: Do I need programming skills?**
A: No. Setup is configuration + copy-paste. Using it is just… using your apps.

**Q: Will this break my current setup?**
A: No. Router routes requests, but if a service is down, it falls back gracefully. You're always safe.

**Q: How much does it cost?**
A: Free. It runs on your Mac. No subscription, no API costs (unless you use Claude/Copilot, which you're doing anyway).

**Q: Will my data be private?**
A: Yes. Everything runs locally by default. Only what you explicitly send to Claude/Copilot leaves your machine.

**Q: Can I turn it off?**
A: Yes. Just stop the router (`docker compose down`). Your apps work like before, just slower and less connected.

**Q: What if I'm not technical enough to set this up myself?**
A: Get a developer friend to build Phase 2 from the spec. They follow a checklist. Once running, setup is config files + you're good.

---

## Next Steps

1. **Share this document** with whoever will build it
2. **Share the technical spec** (phase-1-vision.md, phase-2-core.md, etc.) with the builder
3. **Wait for Week 1 of Phase 2 to be done**
4. **Start using it** — it should feel invisible but helpful

The router is done when you can open Claude Desktop, start chatting, and just notice things are slightly better without understanding why. That's the goal.
