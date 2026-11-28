# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the "DNS zone" screen tools: full values for the App only."""

import pytest
from mcp.client import Client

from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.protocol.app.app_resource import APP_URI
from tests.protocol.app.test_accounts_app_tools import McpAppsSupport
from tests.protocol.tools.livedns.test_livedns_read_tools import (
    DOMAIN,
    Setup,
    add,
    build,
    data,
    error_text,
)

pytestmark = pytest.mark.anyio

DKIM = '"v=DKIM1; k=rsa; p=' + "A" * 400 + '"'
RECORDS = GandiResponse(
    200,
    [
        {"rrset_name": "default._domainkey", "rrset_type": "TXT", "rrset_values": [DKIM]},
        {"rrset_name": "www", "rrset_type": "A", "rrset_values": ["192.0.2.1"]},
    ],
    total_count=2,
)
# The model tools the screen calls (ADR 12, ADR 16): they must stay visible to the App.
SCREEN_TOOLS = {
    "livedns_domains",
    "livedns_record_types",
    "livedns_record_create",
    "livedns_record_replace",
    "livedns_record_delete",
    "livedns_snapshots",
    "livedns_snapshot_create",
    "livedns_snapshot_restore",
}


@pytest.fixture
def setup() -> Setup:
    return build()


def app_client(setup: Setup) -> Client:
    return Client(setup.server, extensions=[McpAppsSupport()])


async def test_the_records_reader_is_bound_to_the_app_only(setup: Setup) -> None:
    async with app_client(setup) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    reader = tools["app_livedns_records"]
    assert (reader.meta or {})["ui"] == {"resourceUri": APP_URI, "visibility": ["app"]}
    assert reader.annotations is not None
    assert reader.annotations.read_only_hint
    for name in SCREEN_TOOLS:
        assert "visibility" not in ((tools[name].meta or {}).get("ui") or {}), name


async def test_the_app_gets_long_values_in_full(setup: Setup) -> None:
    await add(setup)
    setup.gandi.outcomes += [RECORDS, RECORDS]

    async with app_client(setup) as session:
        app = data(
            await session.call_tool(
                "app_livedns_records",
                {"domain": "example.com", "record_type": "txt", "page": 2, "per_page": 10},
            )
        )
        model = data(await session.call_tool("livedns_records", {"domain": "example.com"}))

    assert app["untrusted_data"][0]["rrset_values"] == [DKIM]
    assert app["total_count"] == 2
    assert DKIM not in str(model)
    sent = setup.gandi.calls[0]
    assert sent.path == (*DOMAIN, "records")
    assert sent.query == {"rrset_type": "TXT", "sort_by": "rrset_name", "page": 2, "per_page": 10}


async def test_the_records_reader_is_refused_without_mcp_apps(setup: Setup) -> None:
    await add(setup)
    setup.gandi.outcomes.append(RECORDS)

    async with Client(setup.server) as session:
        result = await session.call_tool("app_livedns_records", {"domain": "example.com"})

    assert "only be used from the Gandi app" in error_text(result)
    assert not setup.gandi.calls


async def test_the_records_reader_refuses_an_unknown_account(setup: Setup) -> None:
    async with app_client(setup) as session:
        result = await session.call_tool(
            "app_livedns_records", {"domain": "example.com", "account": "Nobody"}
        )

    assert result.is_error
    assert not setup.gandi.calls
