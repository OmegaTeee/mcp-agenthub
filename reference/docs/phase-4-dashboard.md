# Phase 4: Dashboard & Observability

> **Status**: Nice-to-have monitoring layer
> **Your Action**: Build only if you need visibility into router health + activity
> **Timeframe**: 1 week (assumes Phase 2 + 3 work)
> **Priority**: LOW — Phase 2 works without this. Add if you find yourself constantly checking logs.

---

## Overview

A simple web dashboard at `http://localhost:9090/dashboard` showing:

- **Service Health** — Which MCP servers are up/down
- **Circuit Breaker Status** — Which services are failing/recovering
- **Enhancement Stats** — Cache hit rate, model usage, slowest operations
- **Recent Activity** — Last 50 requests, response times, errors
- **Quick Actions** — Clear cache, restart services, trigger pipelines

**Technology**: Plain HTML + HTMX (no React, no build step).

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  AI Agent Hub Dashboard                    [Refresh]│
├─────────────────────────────────────────────────────┤
│  Services                  │  Enhancement Stats     │
│  ┌──────────────────────┐  │  ┌────────────────┐    │
│  │ ● Router  healthy    │  │  │ Cache Hits: 847│    │
│  │ ● Ollama  healthy    │  │  │ Miss: 123      │    │
│  │ ● Context7 healthy   │  │  │ Hit Rate: 87%  │    │
│  │ ○ Desktop Cmd degraded  │  │                │    │
│  │ ● Seq Thinking healthy  │  │ Model Usage:   │    │
│  └──────────────────────┘  │  │ llama3.2: 654  │    │
│                            │  │ deepseek: 201  │    │
│  Circuit Breakers          │  └────────────────┘    │
│  ┌──────────────────────┐  │                        │
│  │ context7: CLOSED     │  │  Quick Actions         │
│  │ desktop-cmd: HALF-OP │  │  [Clear Cache]         │
│  │ seq-thinking: CLOSED │  │  [Restart Services]    │
│  └──────────────────────┘  │                        │
├─────────────────────────────────────────────────────┤
│  Recent Activity (last 50)                          │
│  12:34:01 POST /mcp/context7/tools/call  200  45ms  │
│  12:33:58 POST /ollama/enhance           200  1.2s  │
│  12:33:45 GET  /health                   200  12ms  │
└─────────────────────────────────────────────────────┘
```

---

## 4.1 Backend Endpoints for Dashboard

### Existing Endpoints (Phase 2)

```python
GET  /health                # All services' status
GET  /health/{server}       # Single server status
```

### New Dashboard Endpoints

```python
GET  /dashboard             # Main dashboard page (HTML)
GET  /dashboard/health-partial        # HTMX partial (health status only)
GET  /dashboard/stats-partial         # HTMX partial (cache stats only)
GET  /dashboard/activity-partial      # HTMX partial (recent requests only)
POST /dashboard/actions/clear-cache   # Action: clear prompt cache
POST /dashboard/actions/restart/{server}  # Action: restart MCP server
```

### Implementation

```python
# router/dashboard.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime

dashboard_router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")

@dashboard_router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "AI Agent Hub Dashboard"
    })

@dashboard_router.get("/health-partial", response_class=HTMLResponse)
async def health_partial(request: Request):
    """HTMX partial: Service health status."""
    health = await get_all_health()
    return templates.TemplateResponse("partials/health.html", {
        "request": request,
        "services": health
    })

@dashboard_router.get("/stats-partial", response_class=HTMLResponse)
async def stats_partial(request: Request):
    """HTMX partial: Enhancement cache stats."""
    stats = get_cache_stats()
    model_usage = get_model_usage_stats()
    return templates.TemplateResponse("partials/stats.html", {
        "request": request,
        "cache_stats": stats,
        "model_usage": model_usage
    })

@dashboard_router.get("/activity-partial", response_class=HTMLResponse)
async def activity_partial(request: Request):
    """HTMX partial: Recent request activity."""
    activity = get_recent_requests(limit=50)
    return templates.TemplateResponse("partials/activity.html", {
        "request": request,
        "activity": activity
    })

@dashboard_router.post("/actions/clear-cache")
async def clear_cache_action() -> dict:
    """Clear the prompt cache."""
    global cache
    cache.clear()
    return {"status": "success", "message": "Cache cleared"}

@dashboard_router.post("/actions/restart/{server}")
async def restart_server_action(server: str) -> dict:
    """Restart an MCP server."""
    try:
        # Get the server's circuit breaker
        breaker = breaker_registry.get(server)
        # Force reset + restart logic
        await restart_service(server)
        return {"status": "success", "message": f"{server} restarted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

---

## 4.2 Frontend Templates

### Main Page (`templates/dashboard.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        :root {
            --bg: #1a1a2e;
            --card: #16213e;
            --text: #eee;
            --green: #4ecca3;
            --yellow: #ffc107;
            --red: #e74c3c;
            --border: #444;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .header h1 {
            margin: 0;
        }

        .header button {
            background: var(--green);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            color: var(--bg);
            font-weight: bold;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }

        .card h3 {
            margin-top: 0;
            margin-bottom: 15px;
        }

        .status-item {
            display: flex;
            align-items: center;
            padding: 8px;
            margin: 4px 0;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.05);
        }

        .status-dot {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 10px;
        }

        .healthy { background: var(--green); }
        .degraded { background: var(--yellow); }
        .down { background: var(--red); }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }

        td, th {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }

        th {
            background: rgba(255, 255, 255, 0.05);
            font-weight: bold;
        }

        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }

        button {
            background: var(--green);
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            color: var(--bg);
            font-size: 14px;
            transition: opacity 0.2s;
        }

        button:hover {
            opacity: 0.8;
        }

        .htmx-swapping {
            opacity: 0.5;
        }

        .loading {
            text-align: center;
            padding: 20px;
            color: var(--yellow);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Agent Hub Dashboard</h1>
            <button onclick="location.reload()">Refresh All</button>
        </div>

        <div class="grid">
            <!-- Services Health -->
            <div class="card"
                 hx-get="/dashboard/health-partial"
                 hx-trigger="load, every 5s"
                 hx-swap="innerHTML">
                <div class="loading">Loading services...</div>
            </div>

            <!-- Enhancement Stats -->
            <div class="card"
                 hx-get="/dashboard/stats-partial"
                 hx-trigger="load, every 10s"
                 hx-swap="innerHTML">
                <div class="loading">Loading stats...</div>
            </div>
        </div>

        <!-- Quick Actions -->
        <div class="card">
            <h3>Quick Actions</h3>
            <div class="actions">
                <button hx-post="/dashboard/actions/clear-cache"
                        hx-swap="none"
                        hx-confirm="Clear prompt cache?">
                    🗑️ Clear Cache
                </button>
                <button hx-post="/dashboard/actions/restart/context7"
                        hx-swap="none"
                        hx-confirm="Restart Context7?">
                    🔄 Restart Context7
                </button>
                <button hx-post="/dashboard/actions/restart/desktop-commander"
                        hx-swap="none"
                        hx-confirm="Restart Desktop Commander?">
                    🔄 Restart Desktop Cmd
                </button>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="card"
             hx-get="/dashboard/activity-partial"
             hx-trigger="load, every 3s"
             hx-swap="innerHTML">
            <div class="loading">Loading activity...</div>
        </div>
    </div>
</body>
</html>
```

### Health Partial (`templates/partials/health.html`)

```html
<h3>Services</h3>
<div>
{% for service in services %}
    <div class="status-item">
        <span class="status-dot {{ service.status }}"></span>
        <strong>{{ service.name }}</strong>
        <span style="margin-left: auto; color: var(--text-secondary);">
            {{ service.status }}
        </span>
    </div>
{% endfor %}
</div>

<h3 style="margin-top: 20px;">Circuit Breakers</h3>
<table>
    <tr>
        <th>Service</th>
        <th>State</th>
        <th>Failures</th>
        <th>Last Failure</th>
    </tr>
{% for breaker in circuit_breakers %}
    <tr>
        <td>{{ breaker.name }}</td>
        <td>
            <strong>{{ breaker.state }}</strong>
        </td>
        <td>{{ breaker.failures }}</td>
        <td>{{ breaker.last_failure or "—" }}</td>
    </tr>
{% endfor %}
</table>
```

### Stats Partial (`templates/partials/stats.html`)

```html
<h3>Enhancement Cache</h3>
<table>
    <tr>
        <td>Cache Hits</td>
        <td style="text-align: right;">{{ cache_stats.hits }}</td>
    </tr>
    <tr>
        <td>Cache Misses</td>
        <td style="text-align: right;">{{ cache_stats.misses }}</td>
    </tr>
    <tr>
        <td>Hit Rate</td>
        <td style="text-align: right;">{{ "%.1f" | format(cache_stats.hit_rate * 100) }}%</td>
    </tr>
    <tr>
        <td>Cached Prompts</td>
        <td style="text-align: right;">{{ cache_stats.total_cached }}</td>
    </tr>
</table>

<h3 style="margin-top: 20px;">Model Usage</h3>
<table>
    <tr>
        <th>Model</th>
        <th>Calls</th>
        <th>Avg Time</th>
    </tr>
{% for model, stats in model_usage.items() %}
    <tr>
        <td>{{ model }}</td>
        <td style="text-align: right;">{{ stats.calls }}</td>
        <td style="text-align: right;">{{ "%.2f" | format(stats.avg_time * 1000) }}ms</td>
    </tr>
{% endfor %}
</table>
```

### Activity Partial (`templates/partials/activity.html`)

```html
<h3>Recent Activity (last 50 requests)</h3>
<table>
    <tr>
        <th>Time</th>
        <th>Method</th>
        <th>Endpoint</th>
        <th>Status</th>
        <th>Duration</th>
    </tr>
{% for req in activity %}
    <tr>
        <td>{{ req.timestamp }}</td>
        <td>{{ req.method }}</td>
        <td style="font-family: monospace; font-size: 12px;">{{ req.path }}</td>
        <td>
            <span style="color: {{ 'var(--green)' if req.status == 200 else 'var(--red)' }};">
                {{ req.status }}
            </span>
        </td>
        <td style="text-align: right;">{{ "%.0f" | format(req.duration * 1000) }}ms</td>
    </tr>
{% endfor %}
</table>
```

---

## 4.3 Activity Logging

To populate the activity view, track each request:

```python
# router/middleware/logging.py

from datetime import datetime
from collections import deque

class ActivityLog:
    def __init__(self, max_entries: int = 50):
        self.entries = deque(maxlen=max_entries)

    def add(self, method: str, path: str, status: int, duration: float):
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "path": path,
            "status": status,
            "duration": duration
        })

    def get_recent(self, limit: int = 50) -> list:
        return list(reversed(self.entries))[:limit]

activity_log = ActivityLog()

# In FastAPI middleware
@app.middleware("http")
async def log_activity(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    activity_log.add(
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration
    )

    return response
```

---

## 4.4 Cache & Model Stats

```python
# router/stats.py

class CacheStats:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.model_usage = {}

    def record_hit(self):
        self.hits += 1

    def record_miss(self):
        self.misses += 1

    def record_model_use(self, model: str, duration: float):
        if model not in self.model_usage:
            self.model_usage[model] = {"calls": 0, "total_time": 0}
        self.model_usage[model]["calls"] += 1
        self.model_usage[model]["total_time"] += duration

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    @property
    def stats_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hit_rate,
            "total_cached": self.hits + self.misses
        }

    def model_stats(self) -> dict:
        return {
            model: {
                "calls": data["calls"],
                "avg_time": data["total_time"] / data["calls"]
            }
            for model, data in self.model_usage.items()
        }

cache_stats = CacheStats()
```

---

## Success Criteria for Phase 4

You'll know Phase 4 is done when:

1. ✅ `http://localhost:9090/dashboard` loads without errors
2. ✅ Services health updates every 5 seconds
3. ✅ Cache stats update every 10 seconds
4. ✅ Recent activity logs appear in real-time
5. ✅ "Clear Cache" button works
6. ✅ "Restart" buttons successfully restart services
7. ✅ Dashboard feels responsive (HTMX updates don't block UI)

---

## Phase 4 Deliverables

- `router/dashboard.py` — Dashboard endpoints
- `templates/dashboard.html` — Main page
- `templates/partials/health.html` — Health status partial
- `templates/partials/stats.html` — Cache stats partial
- `templates/partials/activity.html` — Recent activity partial
- `router/stats.py` — Stats tracking
- `router/middleware/logging.py` — Activity logging

---

## Clarification: Why Dashboard is Phase 4 (Not Phase 2)

**Reason 1**: A working router is more important than monitoring. You can run the router headless and check health via `curl http://localhost:9090/health`.

**Reason 2**: Dashboard is pure observability — it helps you *understand* the system but doesn't change how it works.

**Reason 3**: If you don't need to see stats or monitor activity, you can skip Phase 4 entirely. Phase 2 + 3 are the core value.

**Decision**: Add Phase 4 only if:
- You want visual insight into router activity
- You're curious about cache hit rates or model usage
- You like dashboards (some people don't)

Don't add Phase 4 "just because." It's a nice-to-have, not essential.

---

## Optional: Upgrade to Qdrant for Persistence

If you're happy with Phase 4 but want dashboard stats to survive router restarts:

1. Move activity log to a database (SQLite, PostgreSQL, or Qdrant)
2. Move cache stats to the same database
3. Dashboard queries the database instead of in-memory structures

**Timeframe**: 2–3 months after Phase 2 is stable. Only if needed.

---

## Next Steps After Phase 4

If you've completed all 4 phases:

1. **Run it for a month** — See what pain points emerge
2. **Add features** based on real usage (not speculation)
3. **Consider upgrades** — Qdrant persistence, learning loops, more pipelines
4. **Share it** — Document the setup so others (or future you) can replicate it

Phase 4 is the capstone. After this, the router is **production‑ready for local use**.
