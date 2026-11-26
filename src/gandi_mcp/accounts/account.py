# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a configured account, without its secret."""

from dataclasses import dataclass, replace

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_reference import AccountReference
from gandi_mcp.accounts.environment import Environment


@dataclass(frozen=True)
class Account:
    """An account of the preferences.

    Attributes:
        name: Name chosen by the user, unique ignoring case.
        environment: Gandi environment targeted by the token.
        read_only: Whether every write operation is refused.
        secret_key: Opaque key of the token in the secret store; it does not change
            when the account is renamed.
        removal_pending: Whether a removal started and did not finish; the account
            can then only be removed again, which completes the removal.
    """

    name: AccountName
    environment: Environment
    read_only: bool
    secret_key: str
    removal_pending: bool = False

    @property
    def reference(self) -> AccountReference:
        """The stable identity of the account and its current environment."""
        return AccountReference(self.secret_key, self.environment)

    def renamed(self, name: AccountName) -> "Account":
        """Return the same account under another name."""
        return replace(self, name=name)
