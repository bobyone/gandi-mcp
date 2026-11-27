<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Build and test the MCP App

The MCP App sources are in [`ui/`](../../ui/); the built, self-contained
`app.html` is committed in `src/gandi_mcp/protocol/app/static/` (see
[ADR 5](../decisions/0005-mcp-app-build.md)). You only need Node to change the
UI.

## Prerequisites

- Node 24 LTS or later (see `ui/.nvmrc`), with `npm` on the `PATH`.
- Install the exact locked dependencies once:

  ```text
  npm ci --prefix ui
  ```

## Commands

| Task | Command |
| --- | --- |
| Lint and format check (ESLint, Prettier) | `npm --prefix ui run lint` |
| Format | `npm --prefix ui run format` |
| Types (TypeScript) | `npm --prefix ui run typecheck` |
| Tests and coverage (threshold 90 %) | `npm --prefix ui test` |
| Build `app.html` and `THIRD_PARTY_NOTICES.md` | `npm --prefix ui run build` |
| UI catalogs | `uv run python scripts/check_ui_translations.py` |
| Runtime npm licenses | `uv run python -m scripts.check_npm_licenses` |
| npm audit (CI) | `npm audit --prefix ui` |

The pre-commit hook runs them all when `ui/` changes, and rebuilds `app.html`:
if the build changed, the hook fails; add the rebuilt files and commit again.

## Structure

- `src/api/`: `AccountsApi` and `DomainsApi` (abstractions) and, in `mcp/`,
  `McpAccountsApi` (app-only account tools) and `McpDomainsApi` (the domain
  tools of the model, see ADR 12).
- `src/components/`: the tabs, the "Accounts" screen (`accounts/`) and the
  "Domains" screen (`domains/`) with their dialogs.
- `src/i18n/`: language negotiation, i18next with ICU messages, and one
  catalog per language in `locales/`; `needs-review.json` lists the
  translations awaiting a native speaker.
- `src/theme.css`: Bootstrap variables mapped to the host style variables.
- `tests/`: Vitest and Testing Library, mirroring `src/`.

## Try it in a client

Run the server from your clone (`uv run gandi-mcp`, see the
[quick-start](../quick-start.md)) in a client that renders MCP Apps, then ask
"open the Gandi app". Use a [sandbox](use-the-sandbox.md) account.
