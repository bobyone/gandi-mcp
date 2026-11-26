# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Start token entry sessions and show their page without involving the model."""

import logging

from gandi_mcp.i18n.message import N_
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.interaction.user_interaction import UserInteraction
from gandi_mcp.token_entry.exceptions import TokenEntryUnavailableError
from gandi_mcp.token_entry.token_entry_page import TokenEntryPage
from gandi_mcp.token_entry.token_entry_session import TokenEntrySession
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget

OPEN_TOKEN_ENTRY_PAGE = N_(
    "Open this page to enter the Personal Access Token of the account {account}."
)

logger = logging.getLogger(__name__)


class TokenEntryService:
    """Open a token entry session for a target account and show its local page."""

    def __init__(
        self,
        sessions: TokenEntrySessions,
        page: TokenEntryPage,
        presenter: LinkPresenter,
        translator: Translator,
    ) -> None:
        self._sessions = sessions
        self._page = page
        self._presenter = presenter
        self._translator = translator

    async def start(
        self,
        target: TokenEntryTarget,
        interaction: UserInteraction | None,
        locale: str | None,
    ) -> TokenEntrySession:
        """Open the session and show its page through URL elicitation or the browser.

        Raises:
            TokenEntryUnavailableError: if the page could not be shown.
        """
        session = self._sessions.open(target)
        url = await self._page.open_token_entry(session, locale)
        message = self._translator.translate(
            OPEN_TOKEN_ENTRY_PAGE, locale, account=str(target.name)
        )
        if not await self._presenter.present(url, message, interaction):
            self._sessions.close(session.session_id)
            raise TokenEntryUnavailableError("the token entry page could not be shown")
        logger.info("token entry session opened (%s)", target.purpose.value)
        return session
