# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Facade of the account rules: the business core of the accounts notion."""

import asyncio
import logging
import uuid
from dataclasses import replace

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_removal import AccountRemoval
from gandi_mcp.accounts.account_summary import AccountSummary
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import (
    AccountNotFoundError,
    DuplicateAccountError,
    NoAccountError,
)
from gandi_mcp.accounts.token_verifier import TokenVerifier
from gandi_mcp.accounts.verified_account import VerifiedAccount
from gandi_mcp.preferences.preferences import Preferences
from gandi_mcp.preferences.preferences_store import PreferencesStore
from gandi_mcp.secrets.exceptions import SecretNotFoundError, SecretStoreError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_store import SecretStore

logger = logging.getLogger(__name__)


def _sorted(accounts: tuple[Account, ...]) -> tuple[Account, ...]:
    return tuple(sorted(accounts, key=lambda account: account.name.key))


class AccountService:
    """Add, change, remove and resolve accounts, keeping the invariants.

    Invariants: names are unique ignoring case; exactly one default account as soon
    as an account exists; an account exists only if its token is stored and Gandi
    accepted it when it was saved. Changes are serialized.
    """

    def __init__(
        self,
        preferences_store: PreferencesStore,
        secret_store: SecretStore,
        token_verifier: TokenVerifier,
    ) -> None:
        self._preferences = preferences_store
        self._secrets = secret_store
        self._verifier = token_verifier
        self._lock = asyncio.Lock()

    async def list(self) -> tuple[AccountSummary, ...]:
        """Return the accounts sorted by name, without secrets."""
        preferences = await self._preferences.load()
        return tuple(
            AccountSummary.of(account, preferences.default_account)
            for account in _sorted(preferences.accounts)
        )

    async def resolve(self, name: AccountName | None = None) -> Account:
        """Return the named account, or the default one when no name is given.

        Raises:
            NoAccountError: if no account is configured.
            AccountNotFoundError: if no account has this name.
        """
        preferences = await self._preferences.load()
        return self._find(preferences, name)

    async def add(self, draft: AccountDraft, token: PersonalAccessToken) -> VerifiedAccount:
        """Verify the token, then keep it and the account; the first one becomes default.

        Raises:
            DuplicateAccountError: if the name is already used.
            TokenRejectedError: if Gandi refuses the token; nothing is kept.
            GandiError, SecretStoreError, PreferencesError: nothing is kept.
        """
        async with self._lock:
            preferences = await self._preferences.load()
            self._check_free(preferences, draft.name)
            identity = await self._verifier.verify(draft.environment, token)
            account = Account(draft.name, draft.environment, draft.read_only, uuid.uuid4().hex)
            await self._secrets.put(account.secret_key, token)
            default = preferences.default_account or account.name
            try:
                await self._preferences.save(
                    Preferences(_sorted((*preferences.accounts, account)), default)
                )
            except Exception:
                await self._forget_token(account.secret_key)
                raise
            logger.info("account added (%s)", account.environment.value)
            return VerifiedAccount(AccountSummary.of(account, default), identity)

    async def rename(self, name: AccountName, new_name: AccountName) -> AccountSummary:
        """Rename an account; changing only the case is allowed.

        Raises:
            AccountNotFoundError, DuplicateAccountError.
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            if new_name != account.name:
                self._check_free(preferences, new_name)
            renamed = account.renamed(new_name)
            default = (
                renamed.name
                if preferences.default_account == account.name
                else preferences.default_account
            )
            await self._save_replacing(preferences, account, renamed, default)
            return AccountSummary.of(renamed, default)

    async def set_default(self, name: AccountName) -> AccountSummary:
        """Make an account the default one.

        Raises:
            AccountNotFoundError, NoAccountError.
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            await self._preferences.save(replace(preferences, default_account=account.name))
            return AccountSummary.of(account, account.name)

    async def set_read_only(self, name: AccountName, read_only: bool) -> AccountSummary:
        """Turn the read-only flag of an account on or off.

        Raises:
            AccountNotFoundError, NoAccountError.
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            changed = replace(account, read_only=read_only)
            await self._save_replacing(preferences, account, changed, preferences.default_account)
            return AccountSummary.of(changed, preferences.default_account)

    async def replace_token(self, name: AccountName, token: PersonalAccessToken) -> VerifiedAccount:
        """Verify a new token in the account environment, then replace the old one.

        Raises:
            AccountNotFoundError, NoAccountError, TokenRejectedError (old token kept),
            GandiError, SecretStoreError.
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            identity = await self._verifier.verify(account.environment, token)
            await self._secrets.put(account.secret_key, token)
            logger.info("account token replaced")
            return VerifiedAccount(
                AccountSummary.of(account, preferences.default_account), identity
            )

    async def change_environment(
        self, name: AccountName, environment: Environment, token: PersonalAccessToken
    ) -> VerifiedAccount:
        """Move an account to another environment, with a token valid there.

        Raises:
            AccountNotFoundError, NoAccountError, TokenRejectedError (nothing changed),
            GandiError, SecretStoreError, PreferencesError (old token restored).
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            identity = await self._verifier.verify(environment, token)
            previous = await self._secrets.get(account.secret_key)
            changed = replace(account, environment=environment)
            await self._secrets.put(account.secret_key, token)
            try:
                await self._save_replacing(
                    preferences, account, changed, preferences.default_account
                )
            except Exception:
                await self._secrets.put(account.secret_key, previous)
                raise
            logger.info("account moved to %s", environment.value)
            return VerifiedAccount(
                AccountSummary.of(changed, preferences.default_account), identity
            )

    async def remove(self, name: AccountName) -> AccountRemoval:
        """Remove an account and its token.

        If it was the default account, the first remaining account in alphabetical
        order becomes the default one.

        Raises:
            AccountNotFoundError, NoAccountError, PreferencesError (nothing removed).
        """
        async with self._lock:
            preferences = await self._preferences.load()
            account = self._find(preferences, name)
            remaining = tuple(item for item in preferences.accounts if item is not account)
            new_default: AccountName | None = None
            default = preferences.default_account
            if default == account.name:
                default = _sorted(remaining)[0].name if remaining else None
                new_default = default
            await self._preferences.save(Preferences(_sorted(remaining), default))
            token_removed = await self._forget_token(account.secret_key)
            logger.info("account removed")
            return AccountRemoval(account.name, new_default, token_removed)

    @staticmethod
    def _find(preferences: Preferences, name: AccountName | None) -> Account:
        if not preferences.accounts:
            raise NoAccountError("no account is configured")
        wanted = name if name is not None else preferences.default_account
        account = preferences.find(wanted) if wanted is not None else None
        if account is None:
            raise AccountNotFoundError(f"no account is named {name}")
        return account

    @staticmethod
    def _check_free(preferences: Preferences, name: AccountName) -> None:
        if preferences.find(name) is not None:
            raise DuplicateAccountError(f"an account is already named {name}")

    async def _save_replacing(
        self,
        preferences: Preferences,
        old: Account,
        new: Account,
        default: AccountName | None,
    ) -> None:
        accounts = tuple(new if item is old else item for item in preferences.accounts)
        await self._preferences.save(Preferences(_sorted(accounts), default))

    async def _forget_token(self, key: str) -> bool:
        try:
            await self._secrets.delete(key)
        except SecretNotFoundError:
            return True
        except SecretStoreError:
            logger.warning("a token could not be removed from the secret store")
            return False
        return True
