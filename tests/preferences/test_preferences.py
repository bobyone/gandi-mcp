# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the preferences invariants."""

import pytest

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.preferences.exceptions import CorruptPreferencesError
from gandi_mcp.preferences.preferences import Preferences

PERSO = Account(AccountName("Perso"), Environment.SANDBOX, False, "k1")
PRO = Account(AccountName("Pro"), Environment.PRODUCTION, True, "k2")


def test_empty_preferences() -> None:
    assert Preferences().accounts == ()
    assert Preferences().default_account is None


def test_finds_an_account_ignoring_case() -> None:
    preferences = Preferences((PERSO, PRO), AccountName("Pro"))

    assert preferences.find(AccountName("PERSO")) == PERSO
    assert preferences.find(AccountName("Other")) is None


@pytest.mark.parametrize(
    ("accounts", "default"),
    [
        ((PERSO, PERSO.renamed(AccountName("PERSO"))), AccountName("Perso")),
        ((PERSO,), None),
        ((PERSO,), AccountName("Pro")),
        ((), AccountName("Perso")),
    ],
)
def test_rejects_broken_invariants(
    accounts: tuple[Account, ...], default: AccountName | None
) -> None:
    with pytest.raises(CorruptPreferencesError):
        Preferences(accounts, default)
