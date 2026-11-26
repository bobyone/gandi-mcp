# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of a way to ask the user for a confirmation."""

from abc import ABC, abstractmethod

from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest


class ConfirmationChannel(ABC):
    """One link of the chain of confirmation channels."""

    @abstractmethod
    def available(self, context: ConfirmationContext) -> bool:
        """Whether this channel can reach the user for this call."""

    @abstractmethod
    async def confirm(
        self, request: ConfirmationRequest, context: ConfirmationContext
    ) -> ConfirmationDecision:
        """Ask the user.

        Raises:
            ConfirmationRefusedError: if the user refused.
            ConfirmationUnavailableError: if the user could not be reached after all.
        """
