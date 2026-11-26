# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the account value object."""

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment


def test_renaming_keeps_the_secret_key() -> None:
    account = Account(AccountName("Perso"), Environment.SANDBOX, False, "key-1")

    renamed = account.renamed(AccountName("Home"))

    assert renamed.name == AccountName("Home")
    assert renamed.secret_key == "key-1"
    assert renamed.environment is Environment.SANDBOX
