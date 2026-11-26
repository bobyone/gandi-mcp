# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of a group of MCP tools for one notion."""

from abc import ABC, abstractmethod

from mcp.server import MCPServer


class ToolModule(ABC):
    """Register the tools of a notion on the MCP server."""

    @abstractmethod
    def register(self, server: MCPServer) -> None:
        """Add the tools of the notion to the server."""
