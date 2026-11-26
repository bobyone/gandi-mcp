<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 8. Declarative endpoint catalogue and one tool per endpoint

- Status: accepted
- Date: 2026-11-26
- Issue: #5

## Context

The Gandi Domain API has 57 endpoints, and the other APIs (LiveDNS, email,
certificates, billing...) bring many more. Most endpoints only differ by their
method, path, accepted parameters and category (read, write, destructive,
billable). MCP tool annotations (`readOnlyHint`, `destructiveHint`) describe a
whole tool.

## Decision

- Each endpoint is described by a `DomainEndpoint` specification: name, method,
  path segments with `{placeholder}` segments, category, accepted query
  parameters, confirmation description, Dry-Run support and follow-up tool. The
  specifications form a catalogue (`operations/domain/domain_endpoints.py`).
- `EndpointOperation` interprets a specification: it checks that every
  placeholder gets a value coming from a validated value object, that each value
  fills one segment, and that only accepted query parameters are sent; the
  `OperationExecutor` then applies the common rules (ADR 4).
- Billable operations, which need a quote, keep a dedicated `BillableOperation`
  class (ADR 7).
- Every endpoint gets its own MCP tool, named like its specification
  (`domain_list`, `domain_glue_record_delete`), with exact annotations.

## Alternatives considered

- **One `Operation` class per endpoint**: explicit, but 57 nearly identical
  files for the Domain API alone.
- **Grouped tools with an `action` parameter** (`manage_glue_records`): fewer
  tools, but their annotations would be wrong for some actions, and clients use
  them to decide what needs the user's attention.

## Consequences

- The tool list is long (about 60 tools for the Domain API); descriptions stay
  short.
- Adding an endpoint is one specification, one tool function and their tests.
