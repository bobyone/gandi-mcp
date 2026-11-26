# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object describing the outcome of an account removal."""

from dataclasses import dataclass

from gandi_mcp.accounts.account_name import AccountName


@dataclass(frozen=True)
class AccountRemoval:
    """What happened when an account was removed.

    Attributes:
        removed: Name of the removed account.
        new_default: The account that became the default one, if the removed account
            was the default and others remain.
    """

    removed: AccountName
    new_default: AccountName | None
