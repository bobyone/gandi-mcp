# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Browser of the operating system, through the standard ``webbrowser`` module."""

import asyncio
import logging
import webbrowser
from urllib.parse import urlsplit

from gandi_mcp.interaction.browser import Browser

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})

logger = logging.getLogger(__name__)


class SystemBrowser(Browser):
    """Open local pages in the default browser of the system.

    Only ``http://127.0.0.1`` and ``http://localhost`` URLs are opened: this browser
    serves the local pages of the server, never an address from untrusted data.
    """

    async def open(self, url: str) -> bool:
        parts = urlsplit(url)
        if parts.scheme != "http" or parts.hostname not in LOCAL_HOSTS:
            raise ValueError("only local pages are opened")
        try:
            opened = await asyncio.to_thread(webbrowser.open, url, 2)
        except webbrowser.Error:
            opened = False
        if not opened:
            logger.warning("no browser could be opened for a local page")
        return opened
