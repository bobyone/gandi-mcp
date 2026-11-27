<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 13. Endpoint catalogue shared by the Gandi APIs

- Status: accepted
- Date: 2026-11-27
- Issues: #14, #6
- Supersedes: [ADR 8](0008-endpoint-catalogue.md) on the two points below

## Context

ADR 8 introduced a declarative catalogue for the Domain API: a `DomainEndpoint`
specification, its interpreter `EndpointOperation` and a `DomainToolRunner`,
with one tool per endpoint. Nothing in them is specific to the Domain API
except their names and location. The LiveDNS API (#6), then the email,
certificate and billing APIs, need the same mechanism. The LiveDNS API also
offers several endpoints doing exactly the same thing: creating a record
through the zone, the name or the name and type path.

## Decision

- The specification becomes `Endpoint`, in `operations/endpoint/`, with
  `EndpointOperation` and its exception `InvalidEndpointArgumentsError`. Each
  API keeps its own catalogue module (`operations/domain/domain_endpoints.py`,
  later `operations/livedns/livedns_endpoints.py`).
- The tool runner becomes `EndpointToolRunner`, in `protocol/tools/`. It
  receives the result filters as an ordered list of `ResultFilter`
  (`content/result_filter.py`), with a `Disclosure` value object carrying what
  the user explicitly asked to see. The container chains `ContactRedactor`,
  then `LongTextFilter` (ADR 10).
- Endpoints that are strictly equivalent (same effect, same category, same
  parameters up to their position in the path) may share one tool. Every
  operation of an API stays available as a tool, and annotations stay exact.
  ADR 8 still applies otherwise: one tool per endpoint.

## Alternatives considered

- **Reuse `DomainEndpoint` for every API**: no change, but a misleading name in
  every new catalogue.
- **One catalogue module for all the APIs**: one place to look, but a long
  file mixing unrelated notions, against the one-notion-per-directory rule.
- **Strictly one tool per endpoint, equivalent ones included**: no exception to
  explain, but identical tools that only lengthen the tool list.

## Consequences

- Moving the files changes imports only: tool names, annotations, results and
  confirmations are unchanged.
- A new filter (for example a secret field filter) is added by implementing
  `ResultFilter` and adding it to `result_filters` in the container.
- A tool covering several equivalent endpoints names the one it calls in its
  specification; the others are listed in the catalogue documentation.
