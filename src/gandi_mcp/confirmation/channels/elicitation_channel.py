# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Confirmation asked through MCP form elicitation."""

from gandi_mcp.confirmation.confirmation_channel import ConfirmationChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import ConfirmationRefusedError
from gandi_mcp.confirmation.messages import confirmation_prompt
from gandi_mcp.i18n.translator import Translator


class ElicitationChannel(ConfirmationChannel):
    """Ask the user in the MCP client, which shows the question to the user."""

    def __init__(self, translator: Translator) -> None:
        self._translator = translator

    def available(self, context: ConfirmationContext) -> bool:
        return context.interaction is not None and context.interaction.supports_confirmation

    async def confirm(
        self, request: ConfirmationRequest, context: ConfirmationContext
    ) -> ConfirmationDecision:
        if context.interaction is None:
            raise ConfirmationRefusedError("no elicitation for this call")
        prompt = confirmation_prompt(self._translator, request, context.locale)
        if not await context.interaction.confirm(prompt):
            raise ConfirmationRefusedError("the user refused the operation")
        return ConfirmationDecision.accept()
