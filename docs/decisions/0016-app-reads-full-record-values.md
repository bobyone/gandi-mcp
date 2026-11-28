<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 16. The MCP App reads full record values through one app-only tool

- Status: accepted
- Date: 2026-11-28
- Issue: #6

## Context

The "DNS zone" screen of the MCP App lists the records of a LiveDNS zone and
lets the user add, edit and delete them, and list, create and restore
snapshots. ADR 12 lets the App call the model tools, whose rules then apply
once. But every model tool result goes through the long text filter (ADR 10):
a DKIM key or a long TXT value is withheld. The App must show and edit those
values in full, and a result of a call made by the App never reaches the
model.

## Decision

- One app-only tool, `app_livedns_records`, reads a page of records with the
  same parameters as `livedns_records` (account, domain, record type, sort
  order, page). Its results keep the untrusted framing and the secret filter,
  but skip the long text filter: the container gives it its own
  `EndpointToolRunner`, which shares the operation executor (account
  resolution) and the catalogue with the model tools.
- It declares `_meta.ui.visibility: ["app"]` and is refused unless the client
  negotiated the MCP Apps extension, like the account tools (ADR 4), so that a
  client that does not render the App cannot hand the full values to its
  model.
- Every other operation of the screen calls the model tools, as in ADR 12:
  `livedns_domains`, `livedns_record_types`, `livedns_record_create`,
  `livedns_record_replace`, `livedns_record_delete`, `livedns_snapshots`,
  `livedns_snapshot_create` and `livedns_snapshot_restore`. Confirmations,
  their counted effect and the snapshot option are asked by the server; the
  App dialog is a preview.

## Alternatives considered

- **An `include_long_values` parameter on `livedns_records`**, like
  `include_contact_details`: no new tool, but the model could set it and
  receive long untrusted texts, against the rule that a long free input never
  reaches the model unreviewed.
- **A full `app_livedns_*` family**: results tailored to the UI, but about
  twelve tools duplicating the model ones, with no secret to protect.

## Consequences

- One rule set for the model and the App; the App parses the untrusted data
  defensively and renders it as text only.
- A change to the parameters of `livedns_records` is mirrored in
  `app_livedns_records`.
- Other screens needing full long texts follow the same pattern: one
  app-only read, model tools for the rest.
