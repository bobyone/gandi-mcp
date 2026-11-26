# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared fixtures."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run asynchronous tests on asyncio, the event loop of the MCP server."""
    return "asyncio"
