# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the money and duration values."""

from decimal import Decimal

import pytest

from gandi_mcp.domains.exceptions import InvalidDomainInputError
from gandi_mcp.domains.money import Money
from gandi_mcp.domains.registration_duration import RegistrationDuration


def test_money_normalizes_its_currency() -> None:
    assert Money(Decimal("24.96"), " eur ") == Money(Decimal("24.96"), "EUR")


@pytest.mark.parametrize(
    ("amount", "currency"),
    [("-1", "EUR"), ("NaN", "EUR"), ("Infinity", "EUR"), ("1", "EURO"), ("1", "E1R")],
)
def test_invalid_money(amount: str, currency: str) -> None:
    with pytest.raises(InvalidDomainInputError):
        Money(Decimal(amount), currency)


@pytest.mark.parametrize("years", [0, 11, True])
def test_invalid_durations(years: int) -> None:
    with pytest.raises(InvalidDomainInputError):
        RegistrationDuration(years)


def test_valid_duration() -> None:
    assert RegistrationDuration(10).years == 10
