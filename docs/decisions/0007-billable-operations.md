<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 7. Billable operations: quote, dry run, price-bound confirmation, re-check

- Status: accepted
- Date: 2026-11-26
- Issue: #5

## Context

Registering, renewing, restoring and transferring a domain charge the prepaid
account of the paying organization. The user must know the exact price before
confirming, and must never pay more than what they confirmed. Gandi prices an
operation with `GET /domain/check` (yearly prices per duration band, taxes
included and excluded), checks a request with the `Dry-Run: 1` header for
registration, renewal and transfer in, and accepts a `price` field only for
registration and transfer in.

## Decision

- A billable operation is a `BillableOperation` (a dedicated class per order:
  registration, renewal, restore, transfer in). It gives its `QuoteRequest`,
  its order path and body, and whether Gandi supports a dry run. It only runs
  through the `OrderExecutor`, which applies algorithm G:
  1. resolve the account and refuse a read-only one; the paying organization
     is the one given with the call, else the account preference, else none
     (`sharing_id`);
  2. quote the order (`QuoteProvider`, `GandiQuoteProvider`): the yearly price
     of the band containing the duration, times the duration; when several
     bands give different prices (registration phases), the quote is refused
     rather than guessed;
  3. on the first call, check it with a dry run when supported; only a `200`
     answer with `status: success` counts as a successful check;
  4. ask for a confirmation whose subject binds the operation, the account
     identity and environment, the price including taxes, its currency and the
     paying organization; its description shows the price formatted in the
     user's language;
  5. quote again just before ordering: any difference, up or down, cancels
     the order (`PriceChangedError`); then check again that the account is
     the same, has the same token as for the quote, and may still write (this
     last check right before the order);
  6. order; registration and transfer in also send `price`, `currency` and,
     for a premium domain, `enforce_premium`, so that Gandi refuses a
     different price.
- A confirmation resumed with its identifier is accepted only if the new quote
  gives the same subject; a different price makes it a mismatch.
- The transfer in uses no dry run: it would run before the authorization code,
  typed with the confirmation (ADR 11), is known.

## Alternatives considered

- **Trusting the `price` field only**: renewal and restore accept none, and a
  quote is needed anyway to show the price before confirming.
- **Confirming without a price**: the user would accept an unknown amount.
- **No re-check**: a price change between the confirmation and the order
  would charge an amount the user never saw.

## Consequences

- An order costs up to four Gandi calls (quote, dry run, quote, order).
- The owner change is not an order: Gandi gives no price for it through
  `/domain/check`. It is a confirmed operation without an amount, checked with a
  dry run, whose confirmation says that Gandi may charge for it depending on the
  extension.
- Assumptions to check on the sandbox: the band prices are yearly, `price` is
  compared before taxes, and `/domain/check` prices renewal, restore and
  transfer.
