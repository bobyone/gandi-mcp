---
name: gandi-mcp-troubleshoot
description: Diagnose gandi-mcp problems (server not starting or not connected, configuration errors, missing tools, keyring unavailable, token refused or expired, token or confirmation page not opening or expired) and read its logs. Use when gandi-mcp fails, disconnects, or behaves unexpectedly.
---

# Troubleshoot gandi-mcp

1. Check the version:
   `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`.
   A failure here points to `uv` or the network; reinstall with the
   `gandi-mcp-install` skill.
2. Exit status 2 at start means a configuration error: the log line names the
   invalid key. Ask the user to compare their file with `gandi-mcp.example.toml`;
   never open their `gandi-mcp.toml` yourself.
3. Logs go to stderr, which the client captures:
   - Claude Code: `/mcp` shows the server status; `claude --debug` shows its
     output;
   - Claude Desktop: the MCP log files of the application (Settings,
     Developer);
   - Codex: the client's session logs.
   For more detail, ask the user to set `logging.level = "DEBUG"` in their
   configuration and restart the client.
4. Account and token problems (the tool message names the remedy):
   - "keyring of the system is unavailable": on Linux, start or install a
     Secret Service (GNOME Keyring, KWallet, KeePassXC) and unlock it; on
     macOS, unlock the login keychain. gandi-mcp never falls back to a file;
   - "Gandi refused the token": the token is invalid, revoked, expired, or
     belongs to the other environment (a sandbox token does not work in
     production). Replace it with `replace_account_token`;
   - "missing from the keyring": the keyring entry was deleted; replace the
     token;
   - "removal of this account was interrupted" (`removal_pending: true` in
     `list_accounts`): remove the account again with `remove_account` to
     finish it;
   - "preferences cannot be read or saved": the preferences file is unreadable
     or was written by a newer version. Ask the user to check it (path:
     `preferences.path`, by default `gandi-mcp/preferences.json` in the user
     configuration directory); never open it yourself.
5. Local pages (token entry, confirmation):
   - nothing opened: the client has no URL elicitation and no browser could be
     opened (for example over SSH). Use a client with the MCP App or
     elicitation, or run gandi-mcp on a computer with a browser;
   - "expired or already used": pages last 10 minutes (token) or 5 minutes
     (confirmation) by default and accept one answer; ask for a new one;
   - "request was refused": the page was opened from another address than
     `127.0.0.1`, or from another site.
6. Logs contain no token nor personal data by design. Still check a log line
   before quoting it in an issue.
7. If the problem persists, use the `gandi-mcp-report-issue` skill.
