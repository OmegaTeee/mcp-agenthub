## Secure storage for Copilot / LLM API keys

Do not store API keys or tokens in `settings.json` (or any checked-in file). Keep them in an environment variable or the OS secret store.

Recommended approaches

- Environment variable (local dev)

  macOS (zsh):

  ```bash
  # temporary for current shell
  export GITHUB_COPILOT_API_KEY="<your-secret>"

  # persist for future GUI apps (so VS Code launched from Dock sees it)
  launchctl setenv GITHUB_COPILOT_API_KEY "<your-secret>"
  ```

- macOS Keychain (recommended for GUI apps)

  ```bash
  # store
  security add-generic-password -a "$USER" -s "com.example/github-copilot" -w "<your-secret>"

  # retrieve (example)
  security find-generic-password -s "com.example/github-copilot" -w
  ```

- VS Code Secret Storage (extension-specific)

  Many extensions can use the VS Code SecretStorage API—check the extension docs. If not supported, prefer the Keychain or env var.

What to do now (quick steps)

1. Remove the key from `settings.json` (already done).
2. Store the key in the Keychain or an env var as shown above.
3. Configure your extension to read the key from the environment or follow the extension's secure auth flow.

Notes

- If you must reference an env var in `settings.json`, some extension settings support `${env:VARNAME}` substitution, but not all extensions will read it—verify extension docs.
- Never commit `settings.json` with secrets to a public repository.

If you want, I can add a small script to fetch the key from Keychain and export it for you when you open a shell. Would you like that? 
