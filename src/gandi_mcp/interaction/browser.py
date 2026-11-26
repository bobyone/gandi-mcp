# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the user's web browser."""

from abc import ABC, abstractmethod


class Browser(ABC):
    """Open a page in the user's browser, without going through the model."""

    @abstractmethod
    async def open(self, url: str) -> bool:
        """Open the URL; ``False`` when no browser could be opened."""
