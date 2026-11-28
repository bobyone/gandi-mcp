<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 14. Confirmation options and effect read before the confirmation

- Status: accepted
- Date: 2026-11-28
- Issue: #6

## Context

A destructive change of a LiveDNS zone (replacing or deleting the zone, the
records of a name, a record or some of its values) cannot be undone, unless a
snapshot of the zone was taken first. Two needs follow:

- the user should decide, outside the model, whether a snapshot is taken
  first: a tool parameter would let the model decide, possibly steered by
  injected text;
- the confirmation should say what will be lost ("replaces the 42 records of
  example.com with 40"), not only which operation runs. That needs a read
  before the confirmation is asked.

The confirmation already carries an optional secret (ADR 11), passed to
`Operation.execute` as a `secret` parameter.

## Decision

- A confirmation request may offer one `ConfirmationOption`: a translatable
  label and a default. Elicitation shows it as a boolean field of the same
  form, and the local page as a checkbox. The decision carries
  `option_chosen`. The mechanism is generic: any operation can offer an option
  with `Operation.confirmation_option()`.
- `Operation.prepare(client, environment, token)` is an asynchronous hook the
  executor calls before `describe()`, on the first call of a confirmed
  operation only. It reads what the description needs and never changes
  anything. It does nothing by default. A Gandi error there stops before any
  confirmation.
- `ConfirmationAnswer` (`operations/confirmation_answer.py`) groups what the
  user gave with an accepted confirmation: the typed `secret` and
  `option_chosen`. It replaces the `secret` parameter of `Operation.execute`.
- The confirmation stays bound to the subject (operation, parameters, account
  identity, environment), not to the content read by `prepare`: a change made
  elsewhere between the confirmation and the operation is accepted as a risk.

## Alternatives considered

- **A `snapshot_first` tool parameter**: simple, but filled by the model, so the
  user's choice is not guaranteed.
- **Always take a snapshot**: safe, but one more call for every change, and the
  user may have automatic snapshots on already.
- **A generic description without counts**: no extra read, but the user does
  not see what will be lost.
- **An `option_chosen` parameter next to `secret`**: fewer changes, but every
  new answer would change the signature of every operation again.
- **Binding the confirmation to the content read**: detects concurrent changes,
  but requires hashing whole zones and asks again after any unrelated change.

## Consequences

- `Operation.execute` takes `answer: ConfirmationAnswer | None` in every
  operation. Billable operations keep their `order(..., secret=...)`: they offer
  no option.
- A confirmed operation with a `prepare` costs one or two more reads.
- Server catalogs gain the option labels; the local page shows a checkbox.
