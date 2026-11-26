<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Quick-start

> Pre-alpha: the server starts but exposes no Gandi tool yet.

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

- **Codex**: add `https://github.com/bobyone/gandi-mcp` as a plugin
  marketplace (see the
  [Codex plugin documentation](https://developers.openai.com/plugins/build/plugins)),
  then install the `gandi-mcp` plugin.

- **Any other MCP client**: run the server with

  ```text
  uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp
  ```

## 3. Configure (optional)

Copy [`config.example.toml`](../config.example.toml) to a `config.toml` of
your choice, adjust it, and pass it with `--config <path>`. Never put your
Personal Access Token in this file.

## 4. Check that it runs

```text
uvx --from git+https://github.com/bobyone/gandi-mcp gandi-mcp --version
```

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
