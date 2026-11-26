# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Apply a token submitted on a local page to its target account."""

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.verified_account import VerifiedAccount
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose


class TokenSubmission:
    """Add the account, replace its token or change its environment."""

    def __init__(self, accounts: AccountService) -> None:
        self._accounts = accounts

    async def submit(self, target: TokenEntryTarget, token: PersonalAccessToken) -> VerifiedAccount:
        """Apply the token as the account rules require.

        Raises:
            AccountError, GandiError, SecretStoreError, PreferencesError: as the
            matching ``AccountService`` operation.
        """
        if target.purpose is TokenPurpose.ADD:
            draft = AccountDraft(target.name, target.environment, target.read_only)
            return await self._accounts.add(draft, token)
        if target.purpose is TokenPurpose.REPLACE:
            return await self._accounts.replace_token(target.name, token)
        return await self._accounts.change_environment(target.name, target.environment, token)
