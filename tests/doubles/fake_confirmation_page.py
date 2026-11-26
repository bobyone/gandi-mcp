# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Confirmation page returning a predictable local URL."""

from dataclasses import dataclass, field

from gandi_mcp.confirmation.confirmation_page import ConfirmationPage
from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation


@dataclass
class FakeConfirmationPage(ConfirmationPage):
    """Return ``http://127.0.0.1:1/confirm/<id>`` and record the pages opened."""

    opened: list[PendingConfirmation] = field(default_factory=list)

    async def open_confirmation(self, pending: PendingConfirmation, locale: str | None) -> str:
        self.opened.append(pending)
        return f"http://127.0.0.1:1/confirm/{pending.confirmation_id}"
