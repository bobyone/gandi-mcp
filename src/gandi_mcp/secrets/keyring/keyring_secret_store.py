# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Secret store backed by the operating system keyring through ``keyring``."""

import asyncio
import logging
from collections.abc import Callable
from typing import Protocol

import keyring
from keyring.errors import KeyringError, PasswordDeleteError

from gandi_mcp.secrets.exceptions import SecretNotFoundError, SecretStoreUnavailableError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_store import SecretStore

DEFAULT_SERVICE = "gandi-mcp"
NOT_FOUND = "no token is stored for this account"

logger = logging.getLogger(__name__)


class KeyringBackend(Protocol):
    """The part of a ``keyring`` backend used by the store."""

    def get_password(self, service: str, username: str) -> str | None: ...

    def set_password(self, service: str, username: str, password: str) -> None: ...

    def delete_password(self, service: str, username: str) -> None: ...


class KeyringSecretStore(SecretStore):
    """Keep tokens in the OS keyring under one service name.

    The keyring is the Windows Credential Manager, the macOS Keychain or the Secret
    Service on Linux. Keyring calls may block (an unlock prompt, for example): they
    run in a worker thread. There is no plaintext fallback: without a usable keyring,
    every operation raises ``SecretStoreUnavailableError``.
    """

    def __init__(
        self, service: str = DEFAULT_SERVICE, backend: KeyringBackend | None = None
    ) -> None:
        """Use the given backend, or the one ``keyring`` selects for the system."""
        self._service = service
        self._backend = backend

    async def _call[T](self, action: Callable[[KeyringBackend], T]) -> T:
        def run() -> T:
            backend = self._backend if self._backend is not None else keyring.get_keyring()
            return action(backend)

        try:
            return await asyncio.to_thread(run)
        except PasswordDeleteError as error:
            raise SecretNotFoundError(NOT_FOUND) from error
        except (KeyringError, RuntimeError, OSError) as error:
            logger.warning("keyring unavailable: %s", type(error).__name__)
            raise SecretStoreUnavailableError(
                "the operating system keyring is unavailable"
            ) from error

    async def get(self, key: str) -> PersonalAccessToken:
        value = await self._call(lambda backend: backend.get_password(self._service, key))
        if value is None:
            raise SecretNotFoundError(NOT_FOUND)
        return PersonalAccessToken(value)

    async def put(self, key: str, token: PersonalAccessToken) -> None:
        await self._call(lambda backend: backend.set_password(self._service, key, token.reveal()))

    async def delete(self, key: str) -> None:
        await self._call(lambda backend: backend.delete_password(self._service, key))
