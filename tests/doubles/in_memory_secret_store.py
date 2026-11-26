# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""In-memory secret store, with switchable failures."""

from gandi_mcp.secrets.exceptions import SecretNotFoundError, SecretStoreUnavailableError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_store import SecretStore


class InMemorySecretStore(SecretStore):
    """Keep tokens in a dictionary; ``unavailable`` makes every call fail."""

    def __init__(self) -> None:
        self.tokens: dict[str, PersonalAccessToken] = {}
        self.unavailable = False

    def _check(self) -> None:
        if self.unavailable:
            raise SecretStoreUnavailableError("unavailable")

    async def get(self, key: str) -> PersonalAccessToken:
        self._check()
        try:
            return self.tokens[key]
        except KeyError as error:
            raise SecretNotFoundError(key) from error

    async def put(self, key: str, token: PersonalAccessToken) -> None:
        self._check()
        self.tokens[key] = token

    async def delete(self, key: str) -> None:
        self._check()
        if self.tokens.pop(key, None) is None:
            raise SecretNotFoundError(key)
