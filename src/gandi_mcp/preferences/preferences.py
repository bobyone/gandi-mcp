# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the preferences: the accounts and the default account."""

from dataclasses import dataclass

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.preferences.exceptions import CorruptPreferencesError


@dataclass(frozen=True)
class Preferences:
    """Local settings without any secret.

    Invariants: account names are unique ignoring case, and the default account is
    one of the accounts, set as soon as an account exists.
    """

    accounts: tuple[Account, ...] = ()
    default_account: AccountName | None = None

    def __post_init__(self) -> None:
        names = [account.name for account in self.accounts]
        if len(set(names)) != len(names):
            raise CorruptPreferencesError("account names must be unique")
        if self.accounts and self.default_account not in names:
            raise CorruptPreferencesError("the default account must be one of the accounts")
        if not self.accounts and self.default_account is not None:
            raise CorruptPreferencesError("there is no default account without accounts")

    def find(self, name: AccountName) -> Account | None:
        """Return the account with this name, ignoring case."""
        return next((account for account in self.accounts if account.name == name), None)
