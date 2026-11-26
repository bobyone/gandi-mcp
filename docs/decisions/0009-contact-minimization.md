<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 9. Minimization of domain contacts and authorization codes sent to the model

- Status: superseded by [ADR 10](0010-model-visible-results.md)
- Date: 2026-11-26
- Issue: #5

## Context

Gandi domain data contains the contacts of each domain (owner, admin, tech,
billing): names, postal addresses, email addresses and phone numbers, often
of private individuals. Tool results are sent to the provider of the LLM
(records of processing, P1). Domain details also contain the authorization
code, which allows a transfer of the domain to another registrar.

## Decision

- Every domain read tool filters the Gandi data with `ContactRedactor` before
  returning it. At any depth, a value under `owner`, `admin`, `bill` or
  `tech` that carries personal fields is reduced to its `type`, `country` and
  `same_as_owner`, with `details: "hidden"`.
- The full contacts are returned only when the tool is called with
  `include_contact_details: true`, which the model sets only when the user
  asks for them.
- The authorization code (`authinfo`) is replaced by `"hidden"` unless
  `include_authorization_code: true` is passed.
- The MCP App shows full contacts: what it displays is not sent to the
  model.

## Alternatives considered

- **Always return the full data**: simpler, but sends personal data that most
  requests do not need.
- **Never return contact details**: the user could no longer check or update
  their contacts through the assistant.

## Consequences

- Answering "who owns this domain?" needs an explicit second call; the tool
  descriptions say so.
- The filtering applies to every response shape, so a new endpoint returning
  contacts is covered without specific code.
