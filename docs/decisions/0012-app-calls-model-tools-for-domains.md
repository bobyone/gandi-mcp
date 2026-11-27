<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 12. The MCP App calls the model tools for domains

- Status: accepted
- Date: 2026-11-27
- Issue: #5

## Context

The "Domains" screen of the MCP App lists the domains of an account, shows
their details with the full contacts, and offers common changes and orders
(automatic renewal, transfer lock, nameservers, renewal, registration). The
server already exposes every one of these operations as a tool for the model,
with their rules: read-only accounts, confirmations outside the model, priced
orders, explained errors, untrusted framing. The account tools of the App are
app-only (ADR 4) because they receive tokens; no secret goes through the
domain screen.

## Decision

- The App calls the domain and organization tools of the model directly:
  `domain_list`, `domain_details`, `domain_check_availability`,
  `domain_autorenew_update`, `domain_transfer_lock`, `domain_transfer_unlock`,
  `domain_nameservers_update`, `domain_renew`, `domain_register`,
  `list_organizations` and `set_paying_organization`. These tools declare no
  `_meta.ui.visibility`, so the MCP Apps specification makes them callable by
  the App as well; a test keeps them visible to it.
- A result of a call made by the App goes to the App only, never to the model.
  The App therefore asks for the full contacts (`include_contact_details`),
  and the owner it registers is typed in the App.
- Confirmed and billable operations follow the same chain as for the model:
  the App dialog is a preview, the server asks for the confirmation
  (elicitation, else local page), and the App resumes the call with the
  returned `confirmation_id`. The price shown in the App is indicative; the
  amount bound to the order is the one of the server confirmation (ADR 7).
- Gandi data stays untrusted in the App: it is rendered as text only.

## Alternatives considered

- **App-only `app_domain_*` tools**, like the account tools: results tailored
  to the UI and a check that the client negotiated MCP Apps, but about fifteen
  duplicated tools to keep in step with the model tools, for no secret to
  protect.

## Consequences

- One implementation of each rule, shared by the model and the App; a change
  to a domain tool's parameters or result changes the App, whose tests
  (`McpDomainsApi`) describe the expected format.
- The App parses the untrusted data defensively: an unexpected or withheld
  field is shown as absent.
- Glue records, DNSSEC, web redirections, transfers and owner changes stay pure
  MCP for now; adding them to the App needs no server change.
