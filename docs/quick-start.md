<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Quick-start

> Pre-alpha: only the account management is available yet.

## 1. Install the prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (it installs
  Python when needed).
- An MCP client: Claude Desktop, Claude Code or Codex.

## 2. Register the server in your client

The plugin of this repository declares the server and its skills, and follows
the `main` branch.

- **Claude Code**:

  ```text
  /plugin marketplace add bobyone/gandi-mcp
  /plugin install gandi-mcp@gandi-mcp
  ```

  Then enable automatic updates of the `gandi-mcp` marketplace in `/plugin`
  (Marketplaces tab).

- **Codex**:

  ```text
  codex plugin marketplace add bobyone/gandi-mcp
  codex plugin add gandi-mcp@gandi-mcp
  ```

  `codex mcp list` then shows the `gandi` server. Update with
  `codex plugin marketplace upgrade`.

- **Any other MCP client**: run the server with

  ```text
  uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp
  ```

## 3. Configure (optional)

Copy [`gandi-mcp.example.toml`](../gandi-mcp.example.toml) to a `gandi-mcp.toml` of
your choice, adjust it, and pass it with `--config <path>`. Never put your
Personal Access Token in this file. Its `[files]` section sets the work
directory, where the zone files and TSIG samples you export are written (see
[export a zone](how-to/export-and-import-a-zone.md)).

## 4. Check that it runs

```text
uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version
```

On Linux, a Secret Service keyring (GNOME Keyring, KWallet or KeePassXC) must
be running: tokens are stored there.

## 5. Add your first account

Ask your assistant: "Add my Gandi sandbox account". A page opens for you to
paste your Personal Access Token; never paste it in the conversation. See
[Add a Gandi account](how-to/add-a-gandi-account.md) and
[Use the Gandi sandbox](how-to/use-the-sandbox.md).

## From a clone (contributors, pull request testing)

```text
git clone https://github.com/bobyone/gandi-mcp
cd gandi-mcp
uv sync
uv run gandi-mcp --version
```

To test a pull request: `gh pr checkout <number>`, `uv sync`, then connect a
client to `uv run --directory <clone> gandi-mcp` (for Claude Code:
`claude mcp add gandi-dev -- uv run --directory <clone> gandi-mcp`).
