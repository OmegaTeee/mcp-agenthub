# LaunchAgent Setup Guide

> **For**: Running the AI Agent Hub as a background service on macOS

---

## Overview

A **LaunchAgent** is macOS's way of running background services automatically when you log in.

**Without LaunchAgent:**

- You manually start the router every time
- If your Mac restarts, router is down
- Apps can't connect until you start it

**With LaunchAgent:**

- Router starts automatically at login
- Runs continuously in the background
- Survives Mac restarts
- Apps always have it available

---

## What We'll Create

A LaunchAgent plist file that:

- ✅ Starts the AI Agent Hub at login
- ✅ Restarts it if it crashes
- ✅ Logs output for debugging
- ✅ Handles Keychain access securely
- ✅ Works with Docker/Colima

---

## Setup Instructions

### Step 1: Create the LaunchAgent Plist

Create the file: `~/.config/launchagents/com.agenthub.plist`

```bash
mkdir -p ~/.config/launchagents
```

Then create `~/.config/launchagents/com.agenthub.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Service identifier -->
    <key>Label</key>
    <string>com.agenthub.service</string>

    <!-- Program to run -->
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/agenthub</string>
        <string>--config</string>
        <string>~/.agenthub/config.json</string>
    </array>

    <!-- Start at login -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Keep running, restart if it crashes -->
    <key>KeepAlive</key>
    <true/>

    <!-- Wait 10 seconds before restarting if it crashes -->
    <key>ThrottleInterval</key>
    <integer>10</integer>

    <!-- Standard output/error logging -->
    <key>StandardOutPath</key>
    <string>~/.agenthub/logs/stdout.log</string>

    <key>StandardErrorPath</key>
    <string>~/.agenthub/logs/stderr.log</string>

    <!-- Environment variables for router -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>

        <key>HOME</key>
        <string>$HOME</string>

        <!-- Ollama access for local models -->
        <key>OLLAMA_HOST</key>
        <string>localhost:11434</string>

        <!-- Docker/Colima socket -->
        <key>DOCKER_HOST</key>
        <string>unix://$HOME/.colima/docker.sock</string>
    </dict>

    <!-- User-level service (runs with your user permissions) -->
    <key>SessionType</key>
    <string>Aqua</string>

    <!-- Keychain access: Run with limited system resources -->
    <key>ProcessType</key>
    <string>Background</string>
</dict>
</plist>
```

### Step 2: Expand ~ in Plist

macOS doesn't expand `~` in plist files automatically. Use this script:

```bash
# Create expand script
cat > ~/.config/launchagents/expand-plist.sh << 'EOF'
#!/bin/bash
PLIST_FILE="$HOME/.config/launchagents/com.agenthub.plist"

# Replace ~ with $HOME path
sed -i '' "s|~|$HOME|g" "$PLIST_FILE"
EOF

chmod +x ~/.config/launchagents/expand-plist.sh

# Run it
~/.config/launchagents/expand-plist.sh
```

**Or do it manually:**

```bash
# Replace ~ with your actual home directory
# For example, if HOME=/Users/yourname:
sed -i '' 's|~|/Users/yourname|g' ~/.config/launchagents/com.agenthub.plist
```

### Step 3: Register the LaunchAgent

Copy the plist to LaunchAgent directory:

```bash
cp ~/.config/launchagents/com.agenthub.plist \
   ~/Library/LaunchAgents/com.agenthub.plist
```

### Step 4: Load the LaunchAgent

```bash
# Load (starts the service)
launchctl load ~/Library/LaunchAgents/com.agenthub.plist

# Verify it's loaded
launchctl list | grep agenthub
# Expected output: com.agenthub.service
```

### Step 5: Create Log Directory

```bash
mkdir -p ~/.agenthub/logs
```

### Step 6: Verify It's Running

```bash
# Check if service is running
launchctl list com.agenthub.service

# Check logs
tail -f ~/.agenthub/logs/stdout.log
tail -f ~/.agenthub/logs/stderr.log

# Test connectivity
curl http://localhost:9090/health
# Expected response: { "status": "ok" }
```

---

## Managing the LaunchAgent

### Start the Service

```bash
launchctl start com.agenthub.service
```

### Stop the Service

```bash
launchctl stop com.agenthub.service
```

### Restart the Service

```bash
launchctl stop com.agenthub.service && launchctl start com.agenthub.service
```

### Unload (Disable Auto-Start)

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.plist
```

### Reload (After Modifying Plist)

```bash
launchctl unload ~/Library/LaunchAgents/com.agenthub.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.plist
```

### View Current Status

```bash
# Detailed status
launchctl list com.agenthub.service

# Expected output:
# {
#   "Label" = "com.agenthub.service";
#   "LimitLoadToSessionType" = "Aqua";
#   "OnDemand" = 0;
#   "PID" = 12345;
#   "PercentCPU" = 0.5;
#   "Program" = "/usr/local/bin/agenthub";
#   ...
# }
```

---

## Keychain Access in LaunchAgent

### The Problem

When running as a LaunchAgent, the router needs access to Keychain credentials (API keys, etc.) but can't prompt the user for permission like a foreground app can.

### The Solution

#### Option 1: Unlock Keychain at Login

Add to your login shell config (`~/.zshrc` or `~/.bash_profile`):

```bash
# Unlock Keychain at login (password-free access)
/usr/bin/security unlock-keychain -p "$PASSWORD" ~/Library/Keychains/login.keychain-db
```

**Problem**: Stores password in shell config (risky).

#### Option 2: Use `security` with Always-Allow

```bash
# Grant permanent "allow all" access to Keychain item
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-token" \
  -A \
  ~/Library/Keychains/login.keychain-db
```

Then manually allow access:

1. First time router accesses, macOS prompts
2. Click "Allow" → "Always Allow"
3. Future accesses don't prompt

**This is the recommended approach.**

#### Option 3: Separate Keychain for Router

Create an unlocked keychain just for router:

```bash
# Create new keychain (password: "router-pass")
security create-keychain -p "router-pass" ~/Library/Keychains/router.keychain-db

# Add credentials to router keychain
security add-generic-password \
  -s "agenthub-context7" \
  -a "default" \
  -w "your-token" \
  ~/Library/Keychains/router.keychain-db

# Unlock router keychain at login (add to shell config)
security unlock-keychain -p "router-pass" ~/Library/Keychains/router.keychain-db
```

**Most secure**: Separate password, but requires manual unlock script.

### Recommended: Option 2 + Unlock Script

Combine both approaches:

```bash
# ~/.zshrc or ~/.bash_profile
# Unlock Keychain quietly at login (if needed)
if ! security list-keychains | grep -q login; then
  security unlock-keychain -p "$KEYCHAIN_PASSWORD" ~/Library/Keychains/login.keychain-db 2>/dev/null
fi
```

Then grant always-allow on credentials (see Option 2).

---

## Docker/Colima Integration

If your router runs in Docker:

### Update ProgramArguments

Instead of `/usr/local/bin/agenthub`, use:

```xml
<key>ProgramArguments</key>
<array>
    <string>/opt/homebrew/bin/docker</string>
    <string>compose</string>
    <string>-f</string>
    <string>/Users/yourname/.agenthub/docker-compose.yml</string>
    <string>up</string>
</array>
```

### Update EnvironmentVariables

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>

    <key>DOCKER_HOST</key>
    <string>unix:///Users/yourname/.colima/docker.sock</string>

    <key>HOME</key>
    <string>/Users/yourname</string>
</dict>
```

### Ensure Colima Starts First

Add to `~/.zshrc`:

```bash
# Start Colima if not running
if ! colima status >/dev/null 2>&1; then
  colima start
fi
```

Or create a separate LaunchAgent for Colima that starts before the router.

---

## Troubleshooting

### LaunchAgent Not Starting

**Check if it's loaded:**

```bash
launchctl list com.agenthub.service
# If not listed, try loading:
launchctl load ~/Library/LaunchAgents/com.agenthub.plist
```

### "Label Already exists"

```bash
# Unload first, then load
launchctl unload ~/Library/LaunchAgents/com.agenthub.plist
launchctl load ~/Library/LaunchAgents/com.agenthub.plist
```

### Logs Show Permission Denied

**Check file permissions:**

```bash
ls -la ~/.agenthub/
# Logs directory should be readable/writable by your user
chmod 755 ~/.agenthub/logs
```

### Router Crashes Repeatedly

**Check crash logs:**

```bash
tail -100 ~/.agenthub/logs/stderr.log
```

**Common causes:**

- Ollama not running (install: `brew install ollama`)
- Port 9090 already in use: `lsof -i :9090`
- Config file path incorrect: verify `~/.agenthub/config.json` exists

### Keychain "Permission Denied"

```bash
# Unlock Keychain manually
security unlock-keychain ~/Library/Keychains/login.keychain-db

# Then restart router
launchctl restart com.agenthub.service
```

### Can't Connect to localhost:9090

```bash
# Check if router is actually running
ps aux | grep agenthub

# Check if port is listening
lsof -i :9090

# Test connection
curl -v http://localhost:9090/health
```

---

## Plist Reference

**Key fields explained:**

| Key                    | Purpose                                                |
| ---------------------- | ------------------------------------------------------ |
| `Label`                | Unique identifier (must match com.agenthub.\*)         |
| `ProgramArguments`     | Command to execute (array, first item is program)      |
| `RunAtLoad`            | Start at login (`true` = yes)                          |
| `KeepAlive`            | Restart if crashes (`true` = yes)                      |
| `ThrottleInterval`     | Seconds before restarting (prevents rapid crash loops) |
| `StandardOutPath`      | Where stdout goes                                      |
| `StandardErrorPath`    | Where stderr goes                                      |
| `EnvironmentVariables` | Dict of env vars for the process                       |
| `SessionType`          | `Aqua` = user session, `Background` = system           |
| `ProcessType`          | `Background` = lower priority, `Standard` = normal     |

---

## See Also

- **keychain-setup.md** — Credential management
- **app-configs.md** — Per-app configuration
- **comparison-table.md** — Decision framework
