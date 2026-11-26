---
name: gandi-mcp-uninstall
description: Remove gandi-mcp cleanly, including its plugin or client registration, cached package, stored tokens and configuration. Use when the user wants to uninstall gandi-mcp or remove all its data.
---

# Uninstall gandi-mcp

Ask for confirmation before each removal; removing tokens is irreversible.

1. Remove the stored Personal Access Tokens first: delete the accounts in
   gandi-mcp (once available), or delete the `gandi-mcp` entries in the OS
   keyring (Windows Credential Manager, macOS Keychain, Secret Service).
2. Remove the client registration:
   - Claude Code: `/plugin uninstall gandi-mcp@gandi-mcp`, then optionally
     `/plugin marketplace remove gandi-mcp`;
   - Codex: uninstall the `gandi-mcp` plugin and remove the marketplace;
   - other clients: delete the `gandi` server entry from their configuration.
3. Remove the cached package: `uv cache clean gandi-mcp`.
4. Ask the user to delete their own `config.toml` if they created one; do not
   read it.
