# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the server of the local pages."""

from abc import abstractmethod

from gandi_mcp.confirmation.confirmation_page import ConfirmationPage
from gandi_mcp.token_entry.token_entry_page import TokenEntryPage


class LocalPageServer(ConfirmationPage, TokenEntryPage):
    """Serve token entry and confirmation pages on ``127.0.0.1``.

    Each page has its own single-use secret code in its URL, distinct from any
    identifier known to the model. The server starts on demand.
    """

    @abstractmethod
    async def close(self) -> None:
        """Stop serving; open pages stop answering."""
