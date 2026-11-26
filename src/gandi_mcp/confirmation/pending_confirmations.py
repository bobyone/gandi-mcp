# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Registry of the confirmations answered on local pages, kept in memory."""

import asyncio
import secrets
import time
from collections.abc import Callable
from dataclasses import replace

from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import (
    ConfirmationExpiredError,
    ConfirmationMismatchError,
    ConfirmationRefusedError,
    SecretInputMissingError,
)
from gandi_mcp.confirmation.pending_confirmation import PendingConfirmation, PendingState
from gandi_mcp.secrets.secret_value import SecretValue

MAX_PENDING = 100

type Scheduler = Callable[[float, Callable[[], None]], None]


def loop_scheduler(delay: float, callback: Callable[[], None]) -> None:
    """Call ``callback`` after ``delay`` seconds on the running event loop, if any."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.call_later(delay, callback)


class PendingConfirmations:
    """Hold pending confirmations until answered, used or expired.

    The user answers on the local page (:meth:`answer`); the operation then gives the
    identifier back (:meth:`consume`), which succeeds once, for the same subject, before
    the deadline: an accepted confirmation not used in time expires too. Nothing
    survives a restart of the server. A confirmation holding a typed secret is
    dropped at its deadline even if nobody asks for it again (ADR 11).
    """

    def __init__(
        self,
        timeout_seconds: float,
        clock: Callable[[], float] = time.monotonic,
        scheduler: Scheduler = loop_scheduler,
    ) -> None:
        """Keep confirmations for ``timeout_seconds``, measured with ``clock``;
        ``scheduler`` runs the removal of secrets at their deadline."""
        self._timeout = timeout_seconds
        self._clock = clock
        self._scheduler = scheduler
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

    def answer(
        self, confirmation_id: str, accepted: bool, secret: SecretValue | None = None
    ) -> PendingConfirmation:
        """Record the user's answer, given on the local page.

        The secret is kept only with an acceptance of a request asking for one, until
        the confirmation is used or expires.

        Raises:
            ConfirmationMismatchError, ConfirmationExpiredError: as :meth:`get`.
            SecretInputMissingError: if an acceptance lacks the secret asked for.
        """
        pending = self.get(confirmation_id)
        asks_secret = pending.request.secret_input is not None
        if accepted and asks_secret and secret is None:
            raise SecretInputMissingError("this confirmation needs a secret")
        state = PendingState.ACCEPTED if accepted else PendingState.REFUSED
        kept = secret if accepted and asks_secret else None
        answered = replace(pending, state=state, secret=kept)
        self._items[confirmation_id] = answered
        if kept is not None:
            self._scheduler(
                max(0.0, answered.deadline - self._clock()),
                lambda: self._expire(confirmation_id, answered),
            )
        return answered

    def consume(self, confirmation_id: str, subject: str) -> PendingConfirmation | None:
        """Use the answer for an operation: the accepted confirmation, ``None`` if pending.

        The returned confirmation carries the typed secret, if any; it is forgotten
        here.

        Raises:
            ConfirmationMismatchError: if unknown, used, or for another subject.
            ConfirmationRefusedError: if the user refused (the identifier is dropped).
            ConfirmationExpiredError: if not answered in time.
        """
        pending = self._live(confirmation_id)
        if pending.request.subject != subject:
            raise ConfirmationMismatchError("this confirmation is for another operation")
        if pending.state is PendingState.PENDING:
            return None
        del self._items[confirmation_id]
        if pending.state is PendingState.REFUSED:
            raise ConfirmationRefusedError("the user refused the operation")
        return pending

    def cancel(self, confirmation_id: str) -> None:
        """Forget a confirmation, for example when its page could not be shown."""
        self._items.pop(confirmation_id, None)

    def _expire(self, confirmation_id: str, answered: PendingConfirmation) -> None:
        """Forget a confirmation holding a secret at its deadline, if still there."""
        if self._items.get(confirmation_id) is answered:
            del self._items[confirmation_id]

    def _live(self, confirmation_id: str) -> PendingConfirmation:
        pending = self._items.get(confirmation_id)
        if pending is None:
            raise ConfirmationMismatchError("unknown or already used confirmation")
        if self._clock() > pending.deadline:
            del self._items[confirmation_id]
            raise ConfirmationExpiredError("the confirmation is no longer valid")
        return pending

    def _purge(self) -> None:
        now = self._clock()
        expired = [key for key, item in self._items.items() if now > item.deadline]
        for key in expired:
            del self._items[key]
