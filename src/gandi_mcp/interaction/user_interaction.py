# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the questions the server asks the user through the MCP client.

Answers come from the user, never from the model: an implementation relies on MCP
elicitation, which the client shows to the user.
"""

from abc import ABC, abstractmethod


class UserInteraction(ABC):
    """Ask the user directly, outside the model context."""

    @property
    @abstractmethod
    def supports_confirmation(self) -> bool:
        """Whether :meth:`confirm` can reach the user (form elicitation)."""

    @property
    @abstractmethod
    def supports_links(self) -> bool:
        """Whether :meth:`open_link` can reach the user (URL elicitation)."""

    @abstractmethod
    async def confirm(self, message: str) -> bool:
        """Ask the user to confirm; ``False`` when refused, cancelled or unanswered."""

    @abstractmethod
    async def confirm_with_option(
        self, message: str, option_label: str, option_default: bool
    ) -> bool | None:
        """Ask the user to confirm, with a yes or no option shown next to it.

        Returns ``None`` when refused, cancelled or unanswered, otherwise whether the
        option was checked.
        """

    @abstractmethod
    async def open_link(self, message: str, url: str) -> bool:
        """Offer a link to the user; ``True`` when the user agreed to open it.

        The link is shown by the client to the user and never reaches the model.
        """
