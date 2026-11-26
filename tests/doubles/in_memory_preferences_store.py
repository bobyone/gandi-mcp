# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""In-memory preferences store, with switchable failures."""

from gandi_mcp.preferences.exceptions import PreferencesUnavailableError
from gandi_mcp.preferences.preferences import Preferences
from gandi_mcp.preferences.preferences_store import PreferencesStore


class InMemoryPreferencesStore(PreferencesStore):
    """Keep the preferences in memory; ``fail_on_save`` makes saving fail."""

    def __init__(self, preferences: Preferences | None = None) -> None:
        self.preferences = preferences or Preferences()
        self.fail_on_save = False
        self.saves = 0

    async def load(self) -> Preferences:
        return self.preferences

    async def save(self, preferences: Preferences) -> None:
        if self.fail_on_save:
            raise PreferencesUnavailableError("unavailable")
        self.preferences = preferences
        self.saves += 1
