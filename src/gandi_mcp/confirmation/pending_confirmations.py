# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Registry of the confirmations answered on local pages, kept in memory."""

import secrets
import time
from collections.abc import Callable
from dataclasses import replace

from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import (
    ConfirmationExpiredError,
    ConfirmationMismatchError,
    ConfirmationRefusedError,
)
from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation, PendingState

MAX_PENDING = 100


class PendingConfirmations:
    """Hold pending confirmations until answered, used or expired.

    The user answers on the local page (:meth:`answer`); the operation then gives the
    identifier back (:meth:`consume`), which succeeds once, for the same subject.
    Nothing survives a restart of the server.
    """

    def __init__(self, timeout_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        """Keep confirmations for ``timeout_seconds``, measured with ``clock``."""
        self._timeout = timeout_seconds
        self._clock = clock
        self._items: dict[str, PendingConfirmation] = {}

    def create(self, request: ConfirmationRequest) -> PendingConfirmation:
        """Register a new pending confirmation with a random identifier."""
        self._purge()
        if len(self._items) >= MAX_PENDING:
            oldest = min(self._items.values(), key=lambda item: item.deadline)
            del self._items[oldest.confirmation_id]
        pending = PendingConfirmation(
            secrets.token_urlsafe(16), request, self._clock() + self._timeout
        )
        self._items[pending.confirmation_id] = pending
        return pending

    def get(self, confirmation_id: str) -> PendingConfirmation:
        """Return a confirmation still waiting for the user's answer.

        Raises:
            ConfirmationMismatchError: if unknown or already answered.
            ConfirmationExpiredError: if its deadline has passed.
        """
        pending = self._live(confirmation_id)
        if pending.state is not PendingState.PENDING:
            raise ConfirmationMismatchError("this confirmation was already answered")
        return pending

    def answer(self, confirmation_id: str, accepted: bool) -> PendingConfirmation:
        """Record the user's answer, given on the local page.

        Raises:
            ConfirmationMismatchError, ConfirmationExpiredError: as :meth:`get`.
        """
        pending = self.get(confirmation_id)
        state = PendingState.ACCEPTED if accepted else PendingState.REFUSED
        answered = replace(pending, state=state)
        self._items[confirmation_id] = answered
        return answered

    def consume(self, confirmation_id: str, subject: str) -> bool:
        """Use the answer for an operation: ``True`` once accepted, ``False`` if pending.

        Raises:
            ConfirmationMismatchError: if unknown, used, or for another subject.
            ConfirmationRefusedError: if the user refused (the identifier is dropped).
            ConfirmationExpiredError: if not answered in time.
        """
        pending = self._live(confirmation_id)
        if pending.request.subject != subject:
            raise ConfirmationMismatchError("this confirmation is for another operation")
        if pending.state is PendingState.PENDING:
            return False
        del self._items[confirmation_id]
        if pending.state is PendingState.REFUSED:
            raise ConfirmationRefusedError("the user refused the operation")
        return True

    def cancel(self, confirmation_id: str) -> None:
        """Forget a confirmation, for example when its page could not be shown."""
        self._items.pop(confirmation_id, None)

    def _live(self, confirmation_id: str) -> PendingConfirmation:
        pending = self._items.get(confirmation_id)
        if pending is None:
            raise ConfirmationMismatchError("unknown or already used confirmation")
        if pending.state is PendingState.PENDING and self._clock() > pending.deadline:
            del self._items[confirmation_id]
            raise ConfirmationExpiredError("the confirmation was not given in time")
        return pending

    def _purge(self) -> None:
        now = self._clock()
        expired = [key for key, item in self._items.items() if now > item.deadline]
        for key in expired:
            del self._items[key]
