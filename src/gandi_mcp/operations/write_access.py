# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Checking again, just before a write, that the account may still write."""

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.exceptions import AccountChangedError, ReadOnlyAccountError


async def still_writable(accounts: AccountService, account: Account) -> Account:
    """The account as it is now, if it is the same one and may still write.

    A confirmation or a quote can take a while: the account may have been made
    read-only, removed, given another token or moved meanwhile.

    Raises:
        ReadOnlyAccountError: if it became read-only.
        AccountChangedError: if it now has another identity or environment.
        AccountNotFoundError, AccountRemovalPendingError: if it was removed.
    """
    current = await accounts.resolve(account.name)
    if current.reference != account.reference:
        raise AccountChangedError(f"the account {account.name} changed meanwhile")
    if current.read_only:
        raise ReadOnlyAccountError(f"the account {account.name} is read-only")
    return current
