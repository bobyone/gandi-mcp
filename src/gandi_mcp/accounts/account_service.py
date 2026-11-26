# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Facade of the account rules: the business core of the accounts notion."""

import asyncio
import contextlib
import logging
import uuid
from dataclasses import replace

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_reference import AccountReference
from gandi_mcp.accounts.account_removal import AccountRemoval
from gandi_mcp.accounts.account_summary import AccountSummary
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import (
    AccountChangedError,
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
    accepted it when it was saved. Changes are serialized, within this process and
    with other processes sharing the preferences: each one loads, changes and saves
    them inside one preferences transaction.
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
        async with self._lock, self._preferences.transaction():
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
                with contextlib.suppress(SecretStoreError):
                    await self._forget_token(account.secret_key, missing_ok=True)
                raise
            logger.info("account added (%s)", account.environment.value)
            return VerifiedAccount(AccountSummary.of(account, default), identity)

    async def update(
        self,
        name: AccountName,
        *,
        new_name: AccountName | None = None,
        read_only: bool | None = None,
        make_default: bool = False,
        expected: AccountReference | None = None,
    ) -> AccountSummary:
        """Rename an account, change its read-only flag and make it the default one.

        Everything is checked first, then applied in one save: a failure changes
        nothing. Changing only the case of the name is allowed.

        Raises:
            AccountNotFoundError, NoAccountError, DuplicateAccountError,
            AccountChangedError (the account no longer matches ``expected``),
            PreferencesError.
        """
        async with self._lock, self._preferences.transaction():
            preferences = await self._preferences.load()
            account = self._find(preferences, name, expected)
            changed = account
            if new_name is not None and new_name.value != account.name.value:
                if new_name != account.name:
                    self._check_free(preferences, new_name)
                changed = changed.renamed(new_name)
            if read_only is not None:
                changed = replace(changed, read_only=read_only)
            default = preferences.default_account
            if make_default or default == account.name:
                default = changed.name
            if changed != account or default != preferences.default_account:
                await self._save_replacing(preferences, account, changed, default)
            return AccountSummary.of(changed, default)

    async def rename(self, name: AccountName, new_name: AccountName) -> AccountSummary:
        """Rename an account; changing only the case is allowed.

        Raises:
            AccountNotFoundError, DuplicateAccountError.
        """
        return await self.update(name, new_name=new_name)

    async def set_default(self, name: AccountName) -> AccountSummary:
        """Make an account the default one.

        Raises:
            AccountNotFoundError, NoAccountError.
        """
        return await self.update(name, make_default=True)

    async def set_read_only(
        self, name: AccountName, read_only: bool, expected: AccountReference | None = None
    ) -> AccountSummary:
        """Turn the read-only flag of an account on or off.

        Raises:
            AccountNotFoundError, NoAccountError, AccountChangedError (the account no
            longer matches ``expected``).
        """
        return await self.update(name, read_only=read_only, expected=expected)

    async def replace_token(
        self,
        name: AccountName,
        token: PersonalAccessToken,
        expected: AccountReference | None = None,
    ) -> VerifiedAccount:
        """Verify a new token in the account environment, then replace the old one.

        Raises:
            AccountNotFoundError, NoAccountError, AccountChangedError (checked before any
            Gandi request), TokenRejectedError (old token kept), GandiError,
            SecretStoreError.
        """
        async with self._lock, self._preferences.transaction():
            preferences = await self._preferences.load()
            account = self._find(preferences, name, expected)
            identity = await self._verifier.verify(account.environment, token)
            await self._secrets.put(account.secret_key, token)
            logger.info("account token replaced")
            return VerifiedAccount(
                AccountSummary.of(account, preferences.default_account), identity
            )

    async def change_environment(
        self,
        name: AccountName,
        environment: Environment,
        token: PersonalAccessToken,
        expected: AccountReference | None = None,
    ) -> VerifiedAccount:
        """Move an account to another environment, with a token valid there.

        Raises:
            AccountNotFoundError, NoAccountError, AccountChangedError (checked before any
            Gandi request), TokenRejectedError (nothing changed), GandiError,
            SecretStoreError, PreferencesError (old token restored).
        """
        async with self._lock, self._preferences.transaction():
            preferences = await self._preferences.load()
            account = self._find(preferences, name, expected)
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

    async def remove(
        self, name: AccountName, expected: AccountReference | None = None
    ) -> AccountRemoval:
        """Remove an account and its token.

        The token is removed first: when the secret store cannot remove it, the
        account is kept, so that the removal can be retried. When saving the
        preferences then fails, the token is put back, so that the account stays
        usable. If it was the default account, the first remaining account in
        alphabetical order becomes the default one.

        Raises:
            AccountNotFoundError, NoAccountError, AccountChangedError,
            SecretStoreError, PreferencesError: nothing removed.
        """
        async with self._lock, self._preferences.transaction():
            preferences = await self._preferences.load()
            account = self._find(preferences, name, expected)
            remaining = tuple(item for item in preferences.accounts if item is not account)
            new_default: AccountName | None = None
            default = preferences.default_account
            if default == account.name:
                default = _sorted(remaining)[0].name if remaining else None
                new_default = default
            try:
                token: PersonalAccessToken | None = await self._secrets.get(account.secret_key)
            except SecretNotFoundError:
                token = None
            await self._forget_token(account.secret_key, missing_ok=True)
            try:
                await self._preferences.save(Preferences(_sorted(remaining), default))
            except Exception:
                if token is not None:
                    await self._restore_token(account.secret_key, token)
                raise
            logger.info("account removed")
            return AccountRemoval(account.name, new_default)

    @staticmethod
    def _find(
        preferences: Preferences,
        name: AccountName | None,
        expected: AccountReference | None = None,
    ) -> Account:
        if not preferences.accounts:
            raise NoAccountError("no account is configured")
        wanted = name if name is not None else preferences.default_account
        account = preferences.find(wanted) if wanted is not None else None
        if account is None:
            raise AccountNotFoundError(f"no account is named {name}")
        if expected is not None and account.reference != expected:
            raise AccountChangedError(f"the account {account.name} changed")
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

    async def _restore_token(self, key: str, token: PersonalAccessToken) -> None:
        try:
            await self._secrets.put(key, token)
        except SecretStoreError:
            logger.error("a token could not be restored in the secret store")

    async def _forget_token(self, key: str, missing_ok: bool = False) -> None:
        try:
            await self._secrets.delete(key)
        except SecretNotFoundError:
            if not missing_ok:
                raise
        except SecretStoreError:
            logger.warning("a token could not be removed from the secret store")
            raise
