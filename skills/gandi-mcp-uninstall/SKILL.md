---
name: gandi-mcp-uninstall
description: Remove gandi-mcp cleanly, including its plugin or client registration, cached package, stored tokens, preferences and configuration. Use when the user wants to uninstall gandi-mcp or remove all its data.
---

# Uninstall gandi-mcp

Ask for confirmation before each removal; removing tokens is irreversible.

1. Remove the stored Personal Access Tokens first: call `list_accounts`, then
   `remove_account` for each account (the user confirms each removal outside
   the conversation). If a result says `token_removed_from_keyring: false`, or
   gandi-mcp no longer starts, ask the user to delete the `gandi-mcp` entries
   in the OS keyring (Windows Credential Manager, macOS Keychain, Secret
   Service) themselves.
2. Ask the user to delete the preferences file (`preferences.json` in the
   `gandi-mcp` folder of the user configuration directory, or the
   `preferences.path` of their configuration); do not read it.
3. Remove the client registration:
   - Claude Code: `/plugin uninstall gandi-mcp@gandi-mcp`, then optionally
     `/plugin marketplace remove gandi-mcp`;
   - Codex: `codex plugin remove gandi-mcp@gandi-mcp`, then optionally
     `codex plugin marketplace remove gandi-mcp`;
   - other clients: delete the `gandi` server entry from their configuration.
4. Remove the cached package: `uv cache clean gandi-mcp`.
5. Ask the user to delete their own `gandi-mcp.toml` if they created one; do not
   read it.
