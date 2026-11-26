# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Token entry page returning a predictable local URL."""

from dataclasses import dataclass, field

from gandi_mcp.token_entry.token_entry_page import TokenEntryPage
from gandi_mcp.token_entry.token_entry_session import TokenEntrySession


@dataclass
class FakeTokenEntryPage(TokenEntryPage):
    """Return ``http://127.0.0.1:1/token/<id>`` and record the sessions."""

    opened: list[TokenEntrySession] = field(default_factory=list)

    async def open_token_entry(self, session: TokenEntrySession, locale: str | None) -> str:
        self.opened.append(session)
        return f"http://127.0.0.1:1/token/{session.session_id}"
