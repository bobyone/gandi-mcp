# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the local page where the user submits a token."""

from abc import ABC, abstractmethod

from gandi_mcp.token_entry.token_entry_session import TokenEntrySession


class TokenEntryPage(ABC):
    """Publish the page of a token entry session."""

    @abstractmethod
    async def open_token_entry(self, session: TokenEntrySession, locale: str | None) -> str:
        """Return the URL of the page, carrying a single-use secret code.

        The URL must never be given to the model.
        """
