# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the secret store, the only place where tokens are kept."""

from abc import ABC, abstractmethod

from gandi_mcp.secrets.personal_access_token import PersonalAccessToken


class SecretStore(ABC):
    """Keep Personal Access Tokens under opaque keys chosen by the caller.

    Every operation may raise ``SecretStoreUnavailableError`` when the store cannot
    be reached.
    """

    @abstractmethod
    async def get(self, key: str) -> PersonalAccessToken:
        """Return the token stored under a key.

        Raises:
            SecretNotFoundError: if no token is stored under the key.
            InvalidTokenFormatError: if the stored value is not a valid token.
        """

    @abstractmethod
    async def put(self, key: str, token: PersonalAccessToken) -> None:
        """Store a token under a key, replacing any previous one."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove the token stored under a key.

        Raises:
            SecretNotFoundError: if no token is stored under the key.
        """
