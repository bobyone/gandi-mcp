# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Price fields of the registration and transfer in bodies."""

from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.gandi.gandi_response import JsonValue


def price_fields(quote: Quote) -> dict[str, JsonValue]:
    """``price`` and ``currency`` (Gandi refuses the order if they differ), and
    ``enforce_premium`` for a premium domain."""
    fields: dict[str, JsonValue] = {
        "price": float(quote.price_before_taxes.amount),
        "currency": quote.price.currency,
    }
    if quote.premium:
        fields["enforce_premium"] = True
    return fields
