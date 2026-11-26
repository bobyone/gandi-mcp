# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Preferences kept in a JSON file, written atomically."""

import contextlib
import json
import logging
import os
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import InvalidAccountNameError
from gandi_mcp.preferences.exceptions import CorruptPreferencesError, PreferencesUnavailableError
from gandi_mcp.preferences.json.blocking_call import run_to_completion
from gandi_mcp.preferences.json.file_lock import FileLock
from gandi_mcp.preferences.preferences import Preferences
from gandi_mcp.preferences.preferences_store import PreferencesStore

FORMAT_VERSION = 1
MAX_FILE_SIZE = 1_000_000
LOCK_TIMEOUT_SECONDS = 10.0

logger = logging.getLogger(__name__)


def _account_from(entry: object) -> Account:
    if not isinstance(entry, dict):
        raise CorruptPreferencesError("an account must be an object")
    name, environment = entry.get("name"), entry.get("environment")
    read_only, secret_key = entry.get("read_only"), entry.get("secret_key")
    if not isinstance(name, str) or not isinstance(environment, str):
        raise CorruptPreferencesError("an account needs a name and an environment")
    if not isinstance(secret_key, str) or not secret_key:
        raise CorruptPreferencesError("an account needs a secret key")
    if not isinstance(read_only, bool):
        raise CorruptPreferencesError("read_only must be a boolean")
    try:
        return Account(AccountName(name), Environment(environment), read_only, secret_key)
    except (InvalidAccountNameError, ValueError) as error:
        raise CorruptPreferencesError("an account has an invalid name or environment") from error


def _from_document(document: object) -> Preferences:
    if not isinstance(document, dict):
        raise CorruptPreferencesError("the preferences must be an object")
    version = document.get("version")
    if version != FORMAT_VERSION:
        raise CorruptPreferencesError(f"unsupported preferences format version: {version!r}")
    entries = document.get("accounts", [])
    default = document.get("default_account")
    if not isinstance(entries, list) or not (default is None or isinstance(default, str)):
        raise CorruptPreferencesError("accounts must be a list and default_account a name")
    try:
        default_name = AccountName(default) if default is not None else None
    except InvalidAccountNameError as error:
        raise CorruptPreferencesError("the default account has an invalid name") from error
    return Preferences(tuple(_account_from(entry) for entry in entries), default_name)


def _to_document(preferences: Preferences) -> dict[str, Any]:
    return {
        "version": FORMAT_VERSION,
        "default_account": str(preferences.default_account)
        if preferences.default_account
        else None,
        "accounts": [
            {
                "name": str(account.name),
                "environment": account.environment.value,
                "read_only": account.read_only,
                "secret_key": account.secret_key,
            }
            for account in preferences.accounts
        ],
    }


class JsonPreferencesStore(PreferencesStore):
    """Keep the preferences in one UTF-8 JSON file.

    A missing file means empty preferences. A file that cannot be understood, or
    written by a newer version, raises ``CorruptPreferencesError`` and is never
    overwritten. Saving writes a temporary file in the same directory, flushes it to
    disk, then replaces the previous file. :meth:`transaction` locks
    ``<file>.lock`` against every other process.
    """

    def __init__(self, path: Path, lock_timeout_seconds: float = LOCK_TIMEOUT_SECONDS) -> None:
        """Use the preferences file at this path; its directory is created on save."""
        self._path = path
        self._lock_timeout = lock_timeout_seconds

    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        lock = FileLock(self._path.with_name(self._path.name + ".lock"), self._lock_timeout)
        # Cancelled while waiting: the lock is released as soon as the worker gets it.
        await run_to_completion(lock.acquire, undo=lambda _: lock.release())
        try:
            yield
        finally:
            lock.release()

    async def load(self) -> Preferences:
        return await run_to_completion(self._load)

    async def save(self, preferences: Preferences) -> None:
        # Cancelled while writing: the write ends before the transaction releases the lock.
        await run_to_completion(lambda: self._save(preferences))

    def _load(self) -> Preferences:
        try:
            if self._path.stat().st_size > MAX_FILE_SIZE:
                raise CorruptPreferencesError("the preferences file is too large")
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return Preferences()
        except (OSError, UnicodeDecodeError) as error:
            raise PreferencesUnavailableError("cannot read the preferences file") from error
        try:
            document = json.loads(text)
        except json.JSONDecodeError as error:
            raise CorruptPreferencesError("the preferences file is not valid JSON") from error
        return _from_document(document)

    def _save(self, preferences: Preferences) -> None:
        content = json.dumps(_to_document(preferences), ensure_ascii=False, indent=2) + "\n"
        temporary: Path | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(
                prefix=f".{self._path.name}.", suffix=".tmp", dir=self._path.parent
            )
            temporary = Path(name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self._path)
        except OSError as error:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise PreferencesUnavailableError("cannot write the preferences file") from error
        logger.info("preferences saved (%d accounts)", len(preferences.accounts))
