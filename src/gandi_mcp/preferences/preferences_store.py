# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the place where preferences are kept."""

from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager

from gandi_mcp.preferences.preferences import Preferences


class PreferencesStore(ABC):
    """Load and save the preferences as a whole."""

    @abstractmethod
    def transaction(self) -> AbstractAsyncContextManager[None]:
        """Hold the preferences exclusively for a read-modify-write.

        The lock is shared with every process using the same preferences, so
        that no concurrent change is lost. Load, change and save inside it.

        Raises:
            PreferencesUnavailableError: if the lock cannot be taken in time.
        """

    @abstractmethod
    async def load(self) -> Preferences:
        """Return the saved preferences, or empty preferences if none were saved.

        Raises:
            CorruptPreferencesError: if the saved preferences cannot be understood.
            PreferencesUnavailableError: if they cannot be read.
        """

    @abstractmethod
    async def save(self, preferences: Preferences) -> None:
        """Replace the saved preferences, atomically.

        Raises:
            PreferencesUnavailableError: if they cannot be written.
        """
