# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Registry of the open token entry sessions, kept in memory."""

import secrets
import time
from collections.abc import Callable

from gandi_mcp.token_entry.exceptions import SessionExpiredError, SessionUsedError
from gandi_mcp.token_entry.token_entry_session import TokenEntrySession
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget

MAX_SESSIONS = 20


class TokenEntrySessions:
    """Open sessions until used or expired; a session is used once, then forgotten."""

    def __init__(self, timeout_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        """Keep sessions for ``timeout_seconds``, measured with ``clock``."""
        self._timeout = timeout_seconds
        self._clock = clock
        self._sessions: dict[str, TokenEntrySession] = {}

    def open(self, target: TokenEntryTarget) -> TokenEntrySession:
        """Open a session with a random identifier."""
        self._purge()
        if len(self._sessions) >= MAX_SESSIONS:
            oldest = min(self._sessions.values(), key=lambda item: item.deadline)
            del self._sessions[oldest.session_id]
        session = TokenEntrySession(
            secrets.token_urlsafe(16), target, self._clock() + self._timeout
        )
        self._sessions[session.session_id] = session
        return session

    def peek(self, session_id: str) -> TokenEntrySession:
        """Return an open session without using it.

        Raises:
            SessionUsedError: if unknown or already used.
            SessionExpiredError: if its deadline has passed.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionUsedError("unknown or already used token entry session")
        if self._clock() > session.deadline:
            del self._sessions[session_id]
            raise SessionExpiredError("the token entry session has expired")
        return session

    def use(self, session_id: str) -> TokenEntrySession:
        """Use an open session: it accepts no other submission afterwards.

        Raises:
            SessionUsedError, SessionExpiredError: as :meth:`peek`.
        """
        session = self.peek(session_id)
        del self._sessions[session_id]
        return session

    def close(self, session_id: str) -> None:
        """Forget a session, for example when its page could not be shown."""
        self._sessions.pop(session_id, None)

    def _purge(self) -> None:
        now = self._clock()
        for key in [key for key, item in self._sessions.items() if now > item.deadline]:
            del self._sessions[key]
