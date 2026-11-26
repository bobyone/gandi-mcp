# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration test of the wiring: the real container builds a working server."""

from pathlib import Path

import pytest
from mcp.client import Client

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.container import user_agent
from gandi_mcp.gandi.http.http_gandi_client import HttpGandiClient
from gandi_mcp.main import build_container, load_configuration
from gandi_mcp.preferences.json.json_preferences_store import JsonPreferencesStore

pytestmark = pytest.mark.anyio


async def test_container_wires_the_server(tmp_path: Path) -> None:
    path = tmp_path / "gandi-mcp.toml"
    path.write_text(
        f'[preferences]\npath = "{(tmp_path / "prefs.json").as_posix()}"\n', encoding="utf-8"
    )
    container = build_container(load_configuration(path))

    async with Client(container.server()) as client:
        tools = {tool.name for tool in (await client.list_tools()).tools}
        accounts = await client.call_tool("list_accounts", {})

    assert "list_accounts" in tools
    assert accounts.structured_content == {"accounts": []}
    assert isinstance(container.preferences_store(), JsonPreferencesStore)
    client_ = container.gandi_client()
    assert isinstance(client_, HttpGandiClient)
    assert set(client_._base_urls) == set(Environment)
    assert container.local_pages() is container.local_pages()


def test_user_agent() -> None:
    assert user_agent("1.2.3") == "gandi-mcp/1.2.3"
