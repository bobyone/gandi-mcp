<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 5. Build and embedding of the MCP App

- Status: accepted
- Date: 2026-11-26
- Issue: #4

## Context

The MCP App is a single HTML document served as the `ui://gandi/app.html`
resource and rendered by the host in a sandboxed frame. It is written in
TypeScript with React, React-Bootstrap and i18next (ADR 2). The personal mode
is installed with `uvx` from Git or PyPI, where Node is usually absent.

## Decision

- The UI lives in `ui/` (npm project, `package-lock.json`, Node 24 LTS pinned in
  `ui/.nvmrc`). Vite and `vite-plugin-singlefile` build one self-contained
  `app.html` (scripts and styles inlined, nothing loaded from the network), so
  its Content Security Policy declares no domain.
- The built `app.html` is **committed** in
  `src/gandi_mcp/protocol/app/static/` and shipped in the Python package, with
  `THIRD_PARTY_NOTICES.md` (license texts of the bundled packages, generated
  from `package-lock.json`). The pre-commit hook rebuilds it whenever `ui/`
  changes: a stale build makes the hook, hence the CI, fail.
- The App talks to the server through app-only tools (`visibility: ["app"]`)
  and confirms destructive actions in its own dialog (ADR 4). App-only tools
  refuse clients that did not negotiate the MCP Apps extension.
- The host theme drives the look: the MCP Apps style variables are mapped to
  Bootstrap CSS variables, and the host theme sets `data-bs-theme`. The
  language is the host locale, then the browser languages, then English.
- UI catalogs are ICU JSON files (`ui/src/i18n/locales/<tag>.json`), checked by
  `scripts/check_ui_translations.py`; runtime npm licenses are checked by
  `scripts/check_npm_licenses.py`, and `npm audit` runs in CI.

## Alternatives considered

- **Build at install time**: no generated file in Git, but every user would
  need Node, and `uvx` installs would fail without it.
- **Build in a release workflow only**: users following `main` (plugin
  updates) would run without a UI.
- **Several files (HTML, JS, CSS)**: smaller diffs, but the host loads one
  resource; serving more would need resource domains in the CSP.

## Consequences

- Pull requests touching `ui/` also change `app.html`; reviewers check the
  sources, the CI checks the build is up to date.
- Contributors touching `ui/` need Node 24 or later; others do not.
- The App is about 1 MB (250 KB compressed), mostly React-Bootstrap and the
  MCP Apps SDK.
