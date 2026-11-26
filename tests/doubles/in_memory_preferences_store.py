# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""In-memory preferences store, with switchable failures."""

import asyncio
import contextlib
from collections.abc import AsyncIterator

from gandi_mcp.preferences.exceptions import PreferencesUnavailableError
from gandi_mcp.preferences.preferences import Preferences
from gandi_mcp.preferences.preferences_store import PreferencesStore


class InMemoryPreferencesStore(PreferencesStore):
    """Keep the preferences in memory.

    ``fail_on_save`` makes every save fail; ``fail_on_save_number`` only the save of
    that rank (1 for the next one).
    """

    def __init__(self, preferences: Preferences | None = None) -> None:
        self.preferences = preferences or Preferences()
        self.fail_on_save = False
        self.fail_on_save_number: int | None = None
        self.saves = 0
        self.transactions = 0
        self._lock = asyncio.Lock()

    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        async with self._lock:
            self.transactions += 1
            yield

    async def load(self) -> Preferences:
        return self.preferences

    async def save(self, preferences: Preferences) -> None:
        if self.fail_on_save_number is not None:
            self.fail_on_save_number -= 1
            if self.fail_on_save_number == 0:
                self.fail_on_save_number = None
                raise PreferencesUnavailableError("unavailable")
        if self.fail_on_save:
            raise PreferencesUnavailableError("unavailable")
        self.preferences = preferences
        self.saves += 1
