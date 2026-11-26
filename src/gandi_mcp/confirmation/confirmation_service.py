# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Chain of confirmation channels."""

import logging
from collections.abc import Sequence

from gandi_mcp.confirmation.confirmation_channel import ConfirmationChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import ConfirmationUnavailableError
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations

logger = logging.getLogger(__name__)


class ConfirmationService:
    """Ask for a confirmation through the first available channel.

    A call carrying a confirmation identifier resumes a confirmation answered on a
    local page instead: it is accepted once, and only for the same subject.
    """

    def __init__(
        self, channels: Sequence[ConfirmationChannel], pending: PendingConfirmations
    ) -> None:
        """Try ``channels`` in order; ``pending`` holds the local page answers."""
        self._channels = tuple(channels)
        self._pending = pending

    async def confirm(
        self,
        request: ConfirmationRequest,
        context: ConfirmationContext,
        confirmation_id: str | None = None,
    ) -> ConfirmationDecision:
        """Return an accepted or pending decision.

        Raises:
            ConfirmationRefusedError, ConfirmationExpiredError,
            ConfirmationMismatchError, ConfirmationUnavailableError.
        """
        if confirmation_id is not None:
            if self._pending.consume(confirmation_id, request.subject):
                return ConfirmationDecision.accept()
            return ConfirmationDecision.pending(confirmation_id)
        for channel in self._channels:
            if channel.available(context):
                decision = await channel.confirm(request, context)
                logger.info(
                    "%s confirmation via %s: %s",
                    request.category.value,
                    type(channel).__name__,
                    "accepted" if decision.accepted else "pending",
                )
                return decision
        raise ConfirmationUnavailableError("no confirmation channel can reach the user")
