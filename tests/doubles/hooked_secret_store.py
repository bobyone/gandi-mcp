# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""In-memory secret store that can run something while a token is being read."""

from collections.abc import Awaitable, Callable

from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_secret_store import InMemorySecretStore


class HookedSecretStore(InMemorySecretStore):
    """Runs ``on_get`` (once) when the token is read for the ``on_read``-th time."""

    def __init__(self) -> None:
        super().__init__()
        self.reads = 0
        self.on_read = 0
        self.on_get: Callable[[], Awaitable[None]] | None = None

    async def get(self, key: str) -> PersonalAccessToken:
        self.reads += 1
        if self.on_get is not None and self.reads == self.on_read:
            hook, self.on_get = self.on_get, None
            await hook()
        return await super().get(key)
