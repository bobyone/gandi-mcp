# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Confirmation already given in a dialog of the MCP App."""

from gandi_mcp.confirmation.confirmation_channel import ConfirmationChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest


class AppChannel(ConfirmationChannel):
    """Accept the calls of app-only tools: the MCP App asked the user before calling.

    App-only tools are only callable by the MCP App, never shown to the model, so the
    user's click in the App dialog is the confirmation (ADR 4).
    """

    def available(self, context: ConfirmationContext) -> bool:
        return context.from_app

    async def confirm(
        self, request: ConfirmationRequest, context: ConfirmationContext
    ) -> ConfirmationDecision:
        return ConfirmationDecision.accept()
