---
name: gandi-mcp-install
description: Install or update the gandi-mcp server and plugin, enable automatic plugin updates, and do the initial configuration. Use when the user wants to set up gandi-mcp, connect it to Claude Desktop, Claude Code or Codex, update it, or asks why its tools are missing.
---

# Install gandi-mcp

Follow the [quick-start](../../docs/quick-start.md); do not reimplement it.

1. Check that `uv` is installed (`uv --version`). If not, point the user to
   <https://docs.astral.sh/uv/getting-started/installation/> and wait.
2. Register the plugin in the user's client, as the quick-start describes:
   - Claude Code: `/plugin marketplace add bobyone/gandi-mcp`, then
     `/plugin install gandi-mcp@gandi-mcp`;
   - Codex: add the repository as a plugin marketplace and install `gandi-mcp`;
   - other clients: configure the command
     `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp`.
3. Ask the user to enable automatic updates of the `gandi-mcp` marketplace
   (Claude Code: `/plugin`, Marketplaces tab). Warn that skills copied by hand
   into a client (folder or archive) are never updated.
4. Optional configuration: copy `config.example.toml` to a `config.toml` and
   add `--config <path>` to the server command. Never read an existing
   `config.toml` or `.env` file yourself. Never ask for the Personal Access
   Token in the conversation: it is entered in the gandi-mcp UI.
5. Verify: `uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`,
   then restart the client and check that the `gandi` server is connected.

To update: the plugin follows the `main` branch; refresh the marketplace
(`/plugin marketplace update gandi-mcp` in Claude Code) and run
`uvx --refresh --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version`.
