---
name: gandi-mcp-install
description: Install or update the gandi-mcp server and plugin, enable automatic plugin updates, and do the initial configuration. Use when the user wants to set up gandi-mcp, connect it to Claude Desktop, Claude Code or Codex, update it, or asks why its tools are missing.
---

# Install gandi-mcp

Follow the [quick-start](../../docs/quick-start.md); do not reimplement it.

1. Check that `uv` is installed (`uv --version`). If not, point the user to
   <https://docs.astral.sh/uv/getting-started/installation/> and wait. On
   Linux, check that a Secret Service keyring runs (GNOME Keyring, KWallet or
   KeePassXC): gandi-mcp stores tokens there and has no other place for them.
2. Register the plugin in the user's client, as the quick-start describes:
   - Claude Code: `/plugin marketplace add bobyone/gandi-mcp`, then
     `/plugin install gandi-mcp@gandi-mcp`;
   - Codex: `codex plugin marketplace add bobyone/gandi-mcp`, then
     `codex plugin add gandi-mcp@gandi-mcp`; `codex mcp list` shows `gandi`;
   - other clients: configure the command
     `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp`.
3. Ask the user to enable automatic updates of the `gandi-mcp` marketplace
   (Claude Code: `/plugin`, Marketplaces tab). Warn that skills copied by hand
   into a client (folder or archive) are never updated.
4. Optional configuration: copy `gandi-mcp.example.toml` to a `gandi-mcp.toml` and
   add `--config <path>` to the server command. Never read an existing
   `gandi-mcp.toml` or `.env` file yourself.
5. Verify: `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`,
   then restart the client and check that the `gandi` server is connected.
6. Add a first account, preferably in the sandbox, with the
   `gandi-mcp-manage-accounts` skill. Never ask for the Personal Access Token
   in the conversation: gandi-mcp shows the user a page to enter it.

To update: the plugin follows the `main` branch; refresh the marketplace
(`/plugin marketplace update gandi-mcp` in Claude Code, `codex plugin marketplace upgrade` in Codex) and run
`uvx --refresh --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`.
