# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the LiveDNS write tools, with an in-memory MCP client and doubles."""

from typing import Any

import pytest
from mcp.client import Client

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.exceptions import GandiConflictError
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.error_presenter import CONFLICT, INVALID_RECORD, READ_ONLY
from gandi_mcp.protocol.tools.endpoint_tool_runner import UNCHANGED_NEXT_STEP
from tests.protocol.tools.livedns.test_livedns_read_tools import (
    DOMAIN,
    ORGANIZATION,
    TOKEN,
    Setup,
    add,
    call,
    data,
    error_text,
)

pytestmark = pytest.mark.anyio

KEY = "7d6a3a3e-1b2c-4d5e-8f90-0123456789ab"
# Arguments, then the expected method, path, body and query of each unconfirmed write.
WRITES: dict[str, tuple[dict[str, Any], str, tuple[str, ...], JsonValue, dict[str, Any] | None]] = {
    "livedns_domain_add": (
        {
            "domain": "Example.com",
            "records": [{"name": "@", "type": "a", "values": ["192.0.2.1"], "ttl": 600}],
            "organization_id": ORGANIZATION,
        },
        "POST",
        ("livedns", "domains"),
        {
            "fqdn": "example.com",
            "zone": {
                "items": [
                    {
                        "rrset_name": "@",
                        "rrset_type": "A",
                        "rrset_values": ["192.0.2.1"],
                        "rrset_ttl": 600,
                    }
                ]
            },
        },
        {"sharing_id": ORGANIZATION},
    ),
    "livedns_automatic_snapshots_update": (
        {"domain": "example.com", "enabled": False},
        "PATCH",
        DOMAIN,
        {"automatic_snapshots": False},
        None,
    ),
    "livedns_record_create": (
        {"domain": "example.com", "name": "WWW", "record_type": "cname", "values": ["@"]},
        "POST",
        (*DOMAIN, "records", "www", "CNAME"),
        {"rrset_values": ["@"]},
        None,
    ),
    "livedns_record_values_add": (
        {
            "domain": "example.com",
            "name": "@",
            "record_type": "TXT",
            "values": ['"v=spf1 -all"'],
            "ttl": 300,
        },
        "PATCH",
        (*DOMAIN, "records", "@", "TXT"),
        {"add_rrset_values": ['"v=spf1 -all"'], "rrset_ttl": 300},
        None,
    ),
    "livedns_domain_verification": (
        {
            "domain": "example.com",
            "name": "_acme-challenge",
            "record_type": "TXT",
            "values": ['"token"'],
        },
        "POST",
        (*DOMAIN, "verification", "_acme-challenge", "TXT"),
        {"rrset_values": ['"token"']},
        None,
    ),
    "livedns_snapshot_create": (
        {"domain": "example.com", "name": "before migration"},
        "POST",
        (*DOMAIN, "snapshots"),
        {"name": "before migration"},
        None,
    ),
    "livedns_snapshot_rename": (
        {"domain": "example.com", "snapshot_id": "snap-1", "name": "kept"},
        "PATCH",
        (*DOMAIN, "snapshots", "snap-1"),
        {"name": "kept"},
        None,
    ),
    "livedns_signing_key_create": (
        {"domain": "example.com", "flags": 257},
        "POST",
        (*DOMAIN, "keys"),
        {"flags": 257},
        None,
    ),
    "livedns_signing_key_restore": (
        {"domain": "example.com", "key_id": "k-1"},
        "PATCH",
        (*DOMAIN, "keys", "k-1"),
        {"deleted": False},
        None,
    ),
    "livedns_secondary_server_add": (
        {"domain": "example.com", "ip": "2001:0db8::0001"},
        "PUT",
        (*DOMAIN, "axfr", "slaves", "2001:db8::1"),
        None,
        None,
    ),
    "livedns_tsig_key_create": ({}, "POST", ("livedns", "axfr", "tsig"), None, None),
    "livedns_domain_tsig_key_add": (
        {"domain": "example.com", "key_id": KEY},
        "PUT",
        (*DOMAIN, "axfr", "tsig", KEY),
        None,
        None,
    ),
}
# Arguments and expected path of each destructive write that is not a zone change.
DESTRUCTIVE: dict[str, tuple[dict[str, Any], tuple[str, ...]]] = {
    "livedns_snapshot_delete": (
        {"domain": "example.com", "snapshot_id": "snap-1"},
        (*DOMAIN, "snapshots", "snap-1"),
    ),
    "livedns_signing_key_delete": (
        {"domain": "example.com", "key_id": "k-1"},
        (*DOMAIN, "keys", "k-1"),
    ),
    "livedns_secondary_server_remove": (
        {"domain": "example.com", "ip": "192.0.2.53"},
        (*DOMAIN, "axfr", "slaves", "192.0.2.53"),
    ),
    "livedns_domain_tsig_key_remove": (
        {"domain": "example.com", "key_id": KEY},
        (*DOMAIN, "axfr", "tsig", KEY),
    ),
}


async def test_one_tool_per_write_endpoint_with_its_annotations(setup: Setup) -> None:
    async with Client(setup.server) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}
    endpoints = {endpoint.name: endpoint for endpoint in livedns_endpoints.WRITE_ENDPOINTS}

    assert set(endpoints) == set(WRITES) | set(DESTRUCTIVE)
    for name, endpoint in endpoints.items():
        annotations = tools[name].annotations
        assert annotations is not None
        assert not annotations.read_only_hint
        assert annotations.destructive_hint is endpoint.category.needs_confirmation
        assert ("confirmation_id" in tools[name].input_schema["properties"]) is (endpoint.confirmed)


@pytest.mark.parametrize("name", sorted(WRITES))
async def test_every_write_sends_its_request(setup: Setup, name: str) -> None:
    await add(setup)
    arguments, method, path, body, query = WRITES[name]
    setup.gandi.outcomes.append(GandiResponse(201, {"message": "done"}))

    result = data(await call(setup, name, arguments))

    sent = setup.gandi.calls[0]
    assert (sent.method, sent.path, sent.body) == (method, path, body)
    if query is not None:
        assert sent.query == query
    assert result["status"] == "done"


@pytest.mark.parametrize("name", sorted(WRITES) + sorted(DESTRUCTIVE))
async def test_writes_are_refused_on_a_read_only_account(setup: Setup, name: str) -> None:
    await setup.accounts.add(
        AccountDraft(AccountName("Watch"), Environment.SANDBOX, read_only=True), TOKEN
    )
    arguments = WRITES[name][0] if name in WRITES else DESTRUCTIVE[name][0]

    text = error_text(await call(setup, name, arguments))

    assert text.endswith(READ_ONLY.singular)
    assert not setup.gandi.calls


@pytest.mark.parametrize("name", sorted(DESTRUCTIVE))
async def test_destructive_writes_wait_for_the_confirmation(setup: Setup, name: str) -> None:
    await add(setup)
    arguments, path = DESTRUCTIVE[name]

    pending = data(await call(setup, name, arguments))

    assert pending["status"] == "confirmation_pending"
    assert not setup.gandi.calls
    setup.pending.answer(pending["confirmation_id"], True)
    done = data(
        await call(setup, name, {**arguments, "confirmation_id": pending["confirmation_id"]})
    )

    assert done["status"] == "done"
    assert (setup.gandi.calls[0].method, setup.gandi.calls[0].path) == ("DELETE", path)


async def test_an_identical_record_creation_changes_nothing(setup: Setup) -> None:
    await add(setup)
    setup.gandi.outcomes.append(GandiResponse(200, {"message": "already exists"}))

    result = data(await call(setup, "livedns_record_create", WRITES["livedns_record_create"][0]))

    assert result["status"] == "unchanged"
    assert result["next_step"] == UNCHANGED_NEXT_STEP


async def test_a_conflicting_record_creation_is_explained(setup: Setup) -> None:
    await add(setup)
    setup.gandi.outcomes.append(GandiConflictError("conflict"))

    text = error_text(
        await call(setup, "livedns_record_create", WRITES["livedns_record_create"][0])
    )

    assert CONFLICT.singular in text


@pytest.mark.parametrize(
    "arguments",
    [
        {"domain": "example.com", "name": "www", "record_type": "A", "values": ["not-an-ip"]},
        {"domain": "example.com", "name": "www", "record_type": "A", "values": ["192.0.2.1\nx"]},
        {"domain": "example.com", "name": "../x", "record_type": "A", "values": ["192.0.2.1"]},
        {
            "domain": "example.com",
            "name": "www",
            "record_type": "A",
            "values": ["192.0.2.1"],
            "ttl": 60,
        },
    ],
)
async def test_invalid_records_never_reach_gandi(setup: Setup, arguments: dict[str, Any]) -> None:
    await add(setup)

    text = error_text(await call(setup, "livedns_record_create", arguments))

    assert text.endswith(INVALID_RECORD.singular)
    assert not setup.gandi.calls
