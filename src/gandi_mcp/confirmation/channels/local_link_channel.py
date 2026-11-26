# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Confirmation answered on a local page, shown without going through the model."""

from gandi_mcp.confirmation.confirmation_channel import ConfirmationChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_page import ConfirmationPage
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import ConfirmationUnavailableError
from gandi_mcp.confirmation.messages import OPEN_CONFIRMATION_PAGE
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.interaction.link_presenter import LinkPresenter


class LocalLinkChannel(ConfirmationChannel):
    """Register a pending confirmation and show its local page to the user.

    The page is offered through URL elicitation, otherwise opened in the browser; its
    link never reaches the model, which only receives the confirmation identifier.
    """

    def __init__(
        self,
        pending: PendingConfirmations,
        page: ConfirmationPage,
        presenter: LinkPresenter,
        translator: Translator,
    ) -> None:
        self._pending = pending
        self._page = page
        self._presenter = presenter
        self._translator = translator

    @property
    def collects_secrets(self) -> bool:
        return True

    def available(self, context: ConfirmationContext) -> bool:
        return True

    async def confirm(
        self, request: ConfirmationRequest, context: ConfirmationContext
    ) -> ConfirmationDecision:
        pending = self._pending.create(request)
        url = await self._page.open_confirmation(pending, context.locale)
        message = self._translator.translate(OPEN_CONFIRMATION_PAGE, context.locale)
        if not await self._presenter.present(url, message, context.interaction):
            self._pending.cancel(pending.confirmation_id)
            raise ConfirmationUnavailableError("the confirmation page could not be shown")
        return ConfirmationDecision.pending(pending.confirmation_id)
