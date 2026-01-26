---
description: 'Guidance for Node / stdio MCP agents: validation checklist, diagnostics, and deployment recommendations.'
applyTo: '**/*.js, **/*.json, configs/vscode-mcp.json'
---

# Node / Stdio MCP Agent — Copilot Instructions

Purpose: Help Copilot and contributors review, validate, and optimize local Node-based
MCP servers that use stdio transports. These instructions are actionable — follow
them before suggesting code or config changes.

Minimal checklist (run before making changes)

- Ensure Node and npx are available on PATH:
  - `which node && node --version`
  - `which npx && npx --version`
- Prefer package names or `npx -y <package>` instead of hard-coded user paths.
- Verify referenced server scripts exist and are executable (examples):
  - `ls -l /Users/<you>/.local/share/mcps/node_modules/…/dist/index.js`
  - `test -f /Users/<you>/.local/bin/mcp-server-fetch && echo ok || echo missing`
- Validate JavaScript syntax for local dist files:
  - `node --check /path/to/dist/index.js`
- Confirm stdio transport is correct in `configs/vscode-mcp.json` (`"type": "stdio"`).

Runtime & portability recommendations

- Avoid absolute, user-home-specific paths in shared configs. Prefer one of:
  1. `npx -y <package>` (runs package without requiring global install)
  2. `node ./node_modules/.bin/<cmd>` from project workspace
  3. Document required local installs and add install snippet to `docs/` or `README.md`
- For custom executables (e.g., `mcp-server-fetch`), prefer installing via `npm` or
  `pipx` (and add a note to docs) rather than symlinking into `~/.local/bin`.
- Make server commands resilient in CI by preferring `npx -y` and version pins.

Security & secrets

- Do not embed API keys in `configs/vscode-mcp.json`. Use environment variables or
  VS Code Secret Storage and document how to set them.
- When suggesting code that calls external services, include timeout and abort
  handling (AbortController for fetch). Document required permissions.

Diagnostics a Copilot review agent should perform automatically

- Check `configs/vscode-mcp.json` entries:
  - `type` exists and is `stdio` for stdio servers
  - `command` is `node` or `npx` (or an absolute executable on PATH)
  - `args` point to valid JS bundles or package names
- For each local JS bundle, run `node --check` and report failures.
- If absolute paths are used, check they are world-readable and executable and
  report that these paths reduce portability.
- Suggest replacements (e.g., convert `/Users/.../node_modules/pkg/dist/index.js` → `npx -y pkg`)
  and provide the exact `configs/vscode-mcp.json` patch that keeps semantics.

Sample quick-fix suggestions (examples Copilot can propose)

- Change absolute Node script to npx (patch):

```diff
--- a/configs/vscode-mcp.json
++++ b/configs/vscode-mcp.json
@@
     "context7": {
       "type": "stdio",
       "command": "npx",
       "args": [
         "-y",
-       "/Users/you/.local/share/mcps/node_modules/@upstash/context7-mcp/dist/index.js"
+       "@upstash/context7-mcp@latest"
       ]
     },
```

- Recommend adding `docs/mcp-servers.md` with `npm install -g` or `npx` instructions.

What to include in a PR

- Explain why the change improves portability (CI, other developers).
- Include a one-line test command to verify the server (e.g. `npx -y @upstash/context7-mcp --help`).
- If changing secrets handling, add usage instructions showing how to set env vars.

When Copilot should not auto-apply fixes

- If the user explicitly depends on a local dev install (e.g., custom patched modules),
  do not replace absolute paths automatically — instead, propose the change and ask.

Example validation script (for reviewer to run locally)

```bash
# quick validate for configured servers
NODE=$(which node); NPX=$(which npx) || NPX='npx'
echo "node: $NODE"; $NODE --version
echo "npx: $NPX"; $NPX --version

for f in \
  "$HOME/.local/share/mcps/node_modules/@upstash/context7-mcp/dist/index.js" \
  "$HOME/.local/share/mcps/node_modules/@wonderwhy-er/desktop-commander/dist/index.js" \
  "$HOME/.local/bin/mcp-server-fetch"; do
  if [ -f "$f" ]; then
    echo "FOUND: $f"; ls -l "$f"
    [[ "$f" == *.js ]] && node --check "$f" || true
  else
    echo "MISSING: $f"
  fi
done
```

Append this file to `.github/instructions` to help Copilot produce consistent, safe
recommendations for Node/stdio MCP agent setups.
