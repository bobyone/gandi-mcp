# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of a group of MCP App resources and tools."""

from abc import ABC, abstractmethod

from mcp.server.apps import Apps


class AppModule(ABC):
    """Register UI resources and UI-bound tools on the MCP Apps extension."""

    @abstractmethod
    def register(self, apps: Apps) -> None:
        """Add the resources and tools of the module to the extension."""
