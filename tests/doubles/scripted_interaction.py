# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""User interaction answering with scripted answers and recording the questions."""

from dataclasses import dataclass, field

from gandi_mcp.interaction.user_interaction import UserInteraction


@dataclass
class ScriptedInteraction(UserInteraction):
    """Answer ``answer`` to every question; flags tell what the client supports."""

    confirmations: bool = True
    links: bool = True
    answer: bool = True
    questions: list[str] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)

    @property
    def supports_confirmation(self) -> bool:
        return self.confirmations

    @property
    def supports_links(self) -> bool:
        return self.links

    async def confirm(self, message: str) -> bool:
        self.questions.append(message)
        return self.answer

    async def open_link(self, message: str, url: str) -> bool:
        self.questions.append(message)
        self.opened.append(url)
        return self.answer
