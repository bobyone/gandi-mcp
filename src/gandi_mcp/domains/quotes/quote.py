# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the price of a billable operation."""

from dataclasses import dataclass

from gandi_mcp.domains.money import Money
from gandi_mcp.domains.quotes.quote_request import QuoteRequest


@dataclass(frozen=True)
class Quote:
    """What an operation would cost, for the requested duration.

    Attributes:
        request: What was priced.
        price: Total price including taxes, for the whole duration.
        price_before_taxes: Total price excluding taxes.
        premium: Whether the domain has a premium price.
        discount: Whether a discount applies.
    """

    request: QuoteRequest
    price: Money
    price_before_taxes: Money
    premium: bool = False
    discount: bool = False
