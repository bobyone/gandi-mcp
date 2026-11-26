<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 2. Technology stack

- Status: accepted
- Date: 2026-11-26
- Issue: #1

## Context

The project needs an MCP server (personal mode), an MCP App UI, and tooling
satisfying the project rules: dependency injection, static typing, locked and
audited dependencies, tests with doubles and coverage, lint and formatting in a
pre-commit hook, internationalization with plural rules, standard logging,
REUSE compliance and license checks.

## Decision

Server in **Python** (3.12+), UI in **TypeScript**.

| Concern | Tool |
| --- | --- |
| MCP server | official `mcp` SDK (`MCPServer`) and its HTTP client, `pydantic` |
| Dependency injection | `dependency-injector` (declarative container) |
| Static typing | `mypy --strict` |
| Packages, lock, audit | `uv`, `uv.lock`, `pip-audit` |
| Tests, doubles, coverage | `pytest`, `unittest.mock`, HTTP mocking, `pytest-cov` (threshold 90 %), in-memory MCP test client |
| Lint, format, hook | `ruff`, `pre-commit` (local hooks calling `uv run`) |
| Internationalization | Babel / gettext catalogs (server messages); i18next with ICU messages (UI) |
| UI library | React + React-Bootstrap, themed by the host variables, bundled as a single HTML file |
| Logs | standard `logging`, to stderr (stdout carries the MCP protocol) |
| Secrets storage | `keyring` (OS keyring) |
| Distribution | Git/PyPI package run with `uvx`, Claude Code and Codex plugins, Claude Desktop extension (`.mcpb`) |
| REUSE, licenses | `reuse lint`, `pip-licenses` through `scripts/check_licenses.py` |
| CI | GitHub Actions on Windows, macOS and Linux; CodeQL; Dependabot |

`GPL-2.0-or-later` allows combining Apache-2.0 dependencies (for example
`opentelemetry-api`, pulled by `mcp`) under the terms of GPL-3.0.

## Alternatives considered

- **TypeScript for both server and UI**: a single ecosystem, and Claude Desktop
  runs Node extensions without an extra runtime, but Node has no standard
  logging library. Rejected by the maintainer.

## Consequences

- Two toolchains (uv and npm) with their own locks, audits and license checks;
  the UI toolchain is added with the first UI (batch 1).
- The Claude Desktop extension needs `uv` (or Python) on the user's computer.
- No signing certificate: releases publish SHA-256 checksums.
- The CPU intermediate model for long free-text inputs is deferred; long inputs
  are either kept in the UI or sent with the user's consent.
