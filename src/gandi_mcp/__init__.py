# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Personal MCP server and MCP App for the Gandi public API."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("gandi-mcp")
except PackageNotFoundError:  # pragma: no cover - only when running from an uninstalled tree
    __version__ = "0.0.0"

__all__ = ["__version__"]
