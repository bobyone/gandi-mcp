<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 6. HTTP client for the Gandi API

- Status: accepted
- Date: 2026-11-26
- Issue: #4

## Context

The Gandi implementations call the Gandi API v5 over HTTPS, asynchronously
like the MCP server. Tests must replace the network without a real Gandi
account. The `mcp` SDK already depends on `httpx2`, which provides an
`AsyncClient` and a `MockTransport`.

## Decision

- `HttpGandiClient` uses `httpx2.AsyncClient`, declared as a direct
  dependency.
- Integration tests replace the network with `httpx2.MockTransport`; the
  `respx` development dependency is removed.
- One client is created per server (container singleton) and reused, with the
  configured timeout (`gandi.timeout_seconds`).

## Alternatives considered

- **`httpx` with `respx`**: mature and well known, but a second HTTP stack next
  to the one the SDK already ships.
- **`aiohttp`**: a new dependency, with a different testing approach.

## Consequences

- No new HTTP dependency; the version follows the `mcp` SDK constraints.
- Tests exercise the real client code with scripted responses.
