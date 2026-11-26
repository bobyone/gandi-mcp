# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of an amount of money."""

from dataclasses import dataclass
from decimal import Decimal

from gandi_mcp.domains.exceptions import InvalidDomainInputError


@dataclass(frozen=True)
class Money:
    """A non-negative amount in a currency (ISO 4217 code, upper case)."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isascii() or not currency.isalpha():  # noqa: PLR2004
            raise InvalidDomainInputError("a currency is a three-letter ISO 4217 code")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidDomainInputError("an amount is a finite non-negative number")
        object.__setattr__(self, "currency", currency)
