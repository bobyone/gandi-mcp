<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 4. Confirmation channels and pending confirmations

- Status: accepted
- Date: 2026-11-26
- Issue: #4

## Context

Destructive and billable operations need the user's explicit confirmation
(ADR 1). The model must never be able to give it: tool calls and their
arguments come from the model, and a model may also have shell tools (Claude
Code, Codex) able to reach local web pages. MCP clients differ: some support
form or URL elicitation, some render the MCP App, some support neither.

## Decision

- Confirmations go through a **chain of channels** (Chain of Responsibility),
  tried in this order:
  1. **MCP App**: an app-only tool (`visibility: ["app"]`, never shown to the
     model) is called by the App after its own dialog; the click is the
     confirmation.
  2. **Elicitation**: a form elicitation naming the account, its environment
     and the operation.
  3. **Local page**: a pending confirmation is registered and its local page
     is shown to the user; the tool returns the confirmation identifier.
- The link of a **local page** (confirmation or token entry session) is never
  returned to the model. It is offered through URL elicitation when the
  client supports it (the client shows it to the user), otherwise the server
  opens it in the user's browser itself. If no browser opens, the operation is
  refused. The page listens on `127.0.0.1` only and carries a single-use code.
- A **pending confirmation** is answered on the page only. The model then
  calls the tool again with the same arguments and the confirmation
  identifier: it is accepted once, for the same subject (the operation and its
  parameters), until it expires (`confirmation.timeout_seconds`). An unknown,
  used or mismatching identifier is refused. Nothing survives a restart.
- Operations are **commands** (`Operation`: name, category, parameters,
  description, execution). `OperationExecutor` applies the rules once: account
  resolution, read-only refusal of writes, confirmation, token, Gandi call,
  untrusted result.

## Alternatives considered

- **Blocking the tool until the page is answered**: the client would wait
  without being able to tell the user anything, and timeouts of MCP clients
  would cut long waits.
- **Returning the page link to the model**, which shows it to the user: a
  model with shell tools could open it and confirm on the user's behalf.
- **Elicitation before the MCP App dialog**: asks the user twice for the same
  action.

## Consequences

- On a computer without a browser and with a client supporting neither
  elicitation nor the MCP App, destructive and billable operations cannot be
  confirmed; the error explains it.
- Trust in app-only tools relies on the host not exposing them to the model,
  as the MCP Apps specification requires. A client that does not render the
  MCP App may still list them to its model: app-only tools therefore refuse
  calls from clients that did not negotiate the MCP Apps extension.
- From protocol revision 2026-07-28, a server cannot send requests to the
  client during a tool call: elicitation goes through input-required results.
  That path is not implemented yet; on such sessions elicitation is treated as
  unavailable and confirmations use the local page. Supporting input-required
  elicitation is deferred to a later decision.
