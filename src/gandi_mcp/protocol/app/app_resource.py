# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The HTML of the MCP App, built from ``ui/`` and shipped in the package."""

from pathlib import Path

from mcp.server.apps import Apps, ResourceCsp

APP_URI = "ui://gandi/app.html"
STATIC_DIRECTORY = Path(__file__).resolve().parent / "static"
APP_FILE = STATIC_DIRECTORY / "app.html"


class AppResourceMissingError(Exception):
    """The built HTML of the MCP App is missing from the package."""


def load_app_html(path: Path = APP_FILE) -> str:
    """Read the built MCP App.

    Raises:
        AppResourceMissingError: if the file was not built (``npm run build`` in ``ui/``).
    """
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise AppResourceMissingError(f"the MCP App is not built: {path.name}") from error


def register_app_resource(apps: Apps, html: str) -> None:
    """Serve the MCP App; it loads nothing from the network (empty CSP domains)."""
    apps.add_html_resource(
        APP_URI,
        html,
        name="gandi-app",
        title="Gandi",
        description="Manage the Gandi accounts of gandi-mcp.",
        csp=ResourceCsp(),
        prefers_border=True,
    )
