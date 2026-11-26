<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 11. Secrets entered with a confirmation

- Status: accepted
- Date: 2026-11-26
- Issue: #5

## Context

Some operations need a secret that only the user knows. The first one is the
authorization code of a domain transferred to Gandi, which gives control over
the domain; mailbox passwords will follow. Passed as a tool parameter, the
secret would go through the model and its provider. The Personal Access Token
already avoids the model through a local page (ADR 3, ADR 4).

## Decision

- A confirmation can ask for a secret: `ConfirmationRequest.secret_input` is an
  optional `SecretInput` (translated label, maximum length). The mechanism is
  generic, so any operation can use it.
- An operation declares its secret with `Operation.secret_input()`. Such an
  operation is always confirmed, whatever its category, and refused on a
  read-only account like any write.
- Only channels that collect secrets outside the model can serve such a
  request (`ConfirmationChannel.collects_secrets`). MCP form elicitation must
  not ask for sensitive data, so the chain skips `ElicitationChannel` and uses
  `LocalLinkChannel`. Its local page shows a password field: it is required to
  confirm, not to refuse, and never written back into the page.
- The secret is a `SecretValue`, masked in `repr` and never serializable. It is
  kept in memory with the accepted confirmation only, and handed to
  `Operation.execute(..., secret)` once, when the confirmation is consumed. It
  is never part of the operation fingerprint, never logged, and never returned
  to the model.

## Alternatives considered

- **A tool parameter**: simplest, but the secret goes through the model and
  its provider.
- **A separate secret-entry session**, like the token entry, followed by the
  quote confirmation: more modular, but two pages and two round trips for the
  user, and state to keep consistent between them.

## Consequences

- The model only sees that a confirmation is pending; the user types the
  secret on the local page, or later in the MCP App confirmation screen.
- An operation needing a secret cannot complete in a client with no browser
  and no URL elicitation: it fails with `ConfirmationUnavailableError`.
