# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of an account as shown to the user and the model: no secret."""

from dataclasses import dataclass

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment


@dataclass(frozen=True)
class AccountSummary:
    """An account without its secret key."""

    name: AccountName
    environment: Environment
    read_only: bool
    is_default: bool

    @classmethod
    def of(cls, account: Account, default: AccountName | None) -> "AccountSummary":
        """Summarize an account, knowing the default account."""
        return cls(account.name, account.environment, account.read_only, account.name == default)
