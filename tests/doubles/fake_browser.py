# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Browser recording the pages it was asked to open."""

from dataclasses import dataclass, field

from gandi_mcp.interaction.browser import Browser


@dataclass
class FakeBrowser(Browser):
    """Record the URLs; ``available`` tells whether opening succeeds."""

    available: bool = True
    opened: list[str] = field(default_factory=list)

    async def open(self, url: str) -> bool:
        self.opened.append(url)
        return self.available
