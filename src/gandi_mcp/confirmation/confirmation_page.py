# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the local page where the user answers a pending confirmation."""

from abc import ABC, abstractmethod

from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation


class ConfirmationPage(ABC):
    """Publish a page asking the user to accept or refuse a pending confirmation."""

    @abstractmethod
    async def open_confirmation(self, pending: PendingConfirmation, locale: str | None) -> str:
        """Return the URL of the page, carrying a single-use secret code.

        The URL must never be given to the model.
        """
