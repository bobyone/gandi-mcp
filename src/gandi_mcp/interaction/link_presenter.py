# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Show a local page to the user without the link ever reaching the model."""

from gandi_mcp.interaction.browser import Browser
from gandi_mcp.interaction.user_interaction import UserInteraction


class LinkPresenter:
    """Offer a local page through URL elicitation, otherwise open it in the browser."""

    def __init__(self, browser: Browser) -> None:
        self._browser = browser

    async def present(self, url: str, message: str, interaction: UserInteraction | None) -> bool:
        """Show the page; ``False`` when the user declined or no browser opened.

        Args:
            url: Local page, carrying its single-use code.
            message: Explanation shown with the link, in the user's language.
            interaction: Questions to the user, when the client supports them.
        """
        if interaction is not None and interaction.supports_links:
            return await interaction.open_link(message, url)
        return await self._browser.open(url)
