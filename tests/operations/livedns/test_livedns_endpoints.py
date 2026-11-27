# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the LiveDNS catalogue and of the TSIG configuration read."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.gandi.media_type import MediaType
from gandi_mcp.livedns.identifiers import TsigKeyId
from gandi_mcp.livedns.tsig_software import TsigSoftware
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.tsig_configuration import TsigConfiguration
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")


def test_the_catalogue_only_reads_and_names_are_unique() -> None:
    endpoints = livedns_endpoints.READ_ENDPOINTS
    names = [endpoint.name for endpoint in endpoints]

    assert len(names) == len(set(names)) == 19
    assert all(name.startswith("livedns_") for name in names)
    assert all(endpoint.category is OperationCategory.READ for endpoint in endpoints)
    assert all(endpoint.method == "GET" for endpoint in endpoints)


def test_only_the_public_nameservers_need_no_token() -> None:
    public = [e.name for e in livedns_endpoints.READ_ENDPOINTS if not e.authenticated]

    assert public == ["livedns_public_nameservers"]


def test_only_the_exports_ask_for_a_zone_file() -> None:
    text = {e.name for e in livedns_endpoints.READ_ENDPOINTS if e.accept is MediaType.TEXT}

    assert text == {"livedns_zone_export", "livedns_snapshot_export"}


async def test_the_tsig_configuration_comes_with_the_secret_of_its_key() -> None:
    client = FakeGandiClient(
        [
            GandiResponse(200, {"id": "k1", "key_name": "transfer", "secret": "s3cr3t"}),
            GandiResponse(200, 'key "transfer" { secret "s3cr3t"; };'),
        ]
    )
    operation = TsigConfiguration(TsigKeyId("k1"), TsigSoftware.BIND, "org-1")

    response = await operation.execute(client, Environment.SANDBOX, TOKEN)

    assert [call.path for call in client.calls] == [
        ("livedns", "axfr", "tsig", "k1"),
        ("livedns", "axfr", "tsig", "k1", "config", "bind"),
    ]
    assert all(call.query == {"sharing_id": "org-1"} for call in client.calls)
    assert response.data == {
        "key_id": "k1",
        "software": "bind",
        "configuration": 'key "transfer" { secret "s3cr3t"; };',
        "secret": "s3cr3t",
    }
    assert operation.category is OperationCategory.READ
    assert operation.name == "livedns_tsig_config"
    assert operation.parameters()["path"] == {"key": "k1", "software": "bind"}
    assert operation.describe().message.singular == "livedns_tsig_config"


async def test_a_missing_configuration_is_unexpected() -> None:
    client = FakeGandiClient([GandiResponse(200, {"id": "k1"}), GandiResponse(200, None)])

    with pytest.raises(GandiUnexpectedResponseError):
        await TsigConfiguration(TsigKeyId("k1"), TsigSoftware.KNOT).execute(
            client, Environment.SANDBOX, TOKEN
        )
