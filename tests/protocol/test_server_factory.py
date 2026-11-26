# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol integration tests with an in-memory MCP test client."""

import pytest
from mcp.client import Client

from gandi_mcp.protocol.server_factory import SERVER_NAME, create_server

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_server_advertises_name_and_version() -> None:
    server = create_server(version="1.2.3")

    async with Client(server) as client:
        info = client.server_info

    assert info is not None
    assert info.name == SERVER_NAME
    assert info.version == "1.2.3"


async def test_server_starts_without_tools() -> None:
    async with Client(create_server(version="1.2.3")) as client:
        tools = await client.list_tools()

    assert tools.tools == []
