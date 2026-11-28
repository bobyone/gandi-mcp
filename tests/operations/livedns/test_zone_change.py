# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the destructive zone changes, with a fake Gandi client."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.exceptions import GandiNotFoundError, GandiUnavailableError
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.livedns.identifiers import SnapshotId
from gandi_mcp.livedns.record import Record
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.record_value import RecordValue
from gandi_mcp.operations.confirmation_answer import ConfirmationAnswer
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns import livedns_messages as messages
from gandi_mcp.operations.livedns.exceptions import SnapshotFailedError
from gandi_mcp.operations.livedns.name_records_change import NameRecordsChange
from gandi_mcp.operations.livedns.record_change import RecordChange
from gandi_mcp.operations.livedns.snapshot_restore import SnapshotRestore
from gandi_mcp.operations.livedns.zone_replacement import ZoneReplacement
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
DOMAIN = DomainName("example.com")
ZONE = ("livedns", "domains", "example.com")
SANDBOX = Environment.SANDBOX


def details(*, automatic: bool) -> GandiResponse:
    return GandiResponse(200, {"fqdn": "example.com", "automatic_snapshots": automatic})


def replacement() -> RecordChange:
    record = Record.of("www", "A", ["192.0.2.1", "192.0.2.2"])
    return RecordChange(
        livedns_endpoints.RECORD_REPLACE,
        DOMAIN,
        record.name,
        record.type,
        body=record.values_json(),
        new_values=record.values,
    )


async def test_a_record_replacement_counts_its_values_before_the_confirmation() -> None:
    client = FakeGandiClient(
        [details(automatic=False), GandiResponse(200, {"rrset_values": ["192.0.2.9"]})]
    )
    change = replacement()

    await change.prepare(client, SANDBOX, TOKEN)

    assert [call.path for call in client.calls] == [ZONE, (*ZONE, "records", "www", "A")]
    assert all(call.method == "GET" for call in client.calls)
    described = change.describe()
    assert described.message == messages.REPLACE_RECORD
    assert described.params == {
        "domain": "example.com",
        "name": "www",
        "type": "A",
        "count": 1,
        "new": 2,
    }
    assert change.confirmation_option().label == messages.SNAPSHOT_FIRST
    assert change.confirmation_option().default


async def test_the_option_label_states_that_automatic_snapshots_are_on() -> None:
    client = FakeGandiClient([details(automatic=True), GandiResponse(200, {"rrset_values": []})])
    change = replacement()

    await change.prepare(client, SANDBOX, TOKEN)

    assert change.confirmation_option().label == messages.SNAPSHOT_FIRST_AUTOMATIC


async def test_a_missing_record_stops_before_the_confirmation() -> None:
    client = FakeGandiClient([details(automatic=False), GandiNotFoundError("missing")])

    with pytest.raises(GandiNotFoundError):
        await replacement().prepare(client, SANDBOX, TOKEN)


async def test_a_snapshot_is_taken_first_when_the_user_chose_it() -> None:
    client = FakeGandiClient([GandiResponse(201, {"id": "snap-9"}), GandiResponse(201, None)])

    response = await replacement().execute(
        client, SANDBOX, TOKEN, ConfirmationAnswer(option_chosen=True)
    )

    assert [(call.method, call.path) for call in client.calls] == [
        ("POST", (*ZONE, "snapshots")),
        ("PUT", (*ZONE, "records", "www", "A")),
    ]
    assert client.calls[1].body == {"rrset_values": ["192.0.2.1", "192.0.2.2"]}
    assert response.data == {"result": None, "snapshot_id": "snap-9"}


async def test_no_snapshot_without_the_choice() -> None:
    client = FakeGandiClient([GandiResponse(201, None)])

    await replacement().execute(client, SANDBOX, TOKEN, ConfirmationAnswer(option_chosen=False))
    await replacement().execute(client, SANDBOX, TOKEN)

    assert [call.method for call in client.calls] == ["PUT", "PUT"]


async def test_a_failed_snapshot_changes_nothing() -> None:
    client = FakeGandiClient([GandiUnavailableError("down")])

    with pytest.raises(SnapshotFailedError):
        await replacement().execute(client, SANDBOX, TOKEN, ConfirmationAnswer(option_chosen=True))

    assert [call.method for call in client.calls] == ["POST"]


async def test_a_value_removal_counts_the_removed_and_left_values() -> None:
    client = FakeGandiClient(
        [
            details(automatic=False),
            GandiResponse(200, {"rrset_values": ["10 a.example.", "20 b.example."]}),
        ]
    )
    removed = (RecordValue("20 b.example."), RecordValue("30 c.example."))
    change = RecordChange(
        livedns_endpoints.RECORD_VALUES_REMOVE,
        DOMAIN,
        RecordName("@"),
        RecordType.MX,
        body={"remove_rrset_values": [value.value for value in removed]},
        removed_values=removed,
    )

    await change.prepare(client, SANDBOX, TOKEN)

    assert change.describe().params["count"] == 1
    assert change.describe().params["left"] == 1


async def test_the_records_of_a_name_are_counted() -> None:
    client = FakeGandiClient([details(automatic=False), GandiResponse(200, [{}, {}, {}])])
    change = NameRecordsChange(livedns_endpoints.NAME_RECORDS_DELETE, DOMAIN, RecordName("_dmarc"))

    await change.prepare(client, SANDBOX, TOKEN)

    assert client.calls[1].path == (*ZONE, "records", "_dmarc")
    assert change.describe().params == {"domain": "example.com", "name": "_dmarc", "count": 3}


async def test_a_zone_replacement_counts_the_zone_from_its_total() -> None:
    client = FakeGandiClient([details(automatic=False), GandiResponse(200, [{}], total_count=42)])
    change = ZoneReplacement(
        livedns_endpoints.ZONE_REPLACE, DOMAIN, body={"items": []}, new_count=40
    )

    await change.prepare(client, SANDBOX, TOKEN)

    assert client.calls[1].query == {"page": 1, "per_page": 1}
    assert change.describe().params == {"domain": "example.com", "count": 42, "new": 40}


async def test_an_import_sends_the_zone_file_and_is_bound_to_its_content() -> None:
    client = FakeGandiClient()
    zone = "@ 300 IN A 192.0.2.1\n"
    change = ZoneReplacement(
        livedns_endpoints.ZONE_IMPORT, DOMAIN, text_body=zone, new_count=1, params={"file": "z"}
    )
    other = ZoneReplacement(
        livedns_endpoints.ZONE_IMPORT, DOMAIN, text_body=zone + " ", new_count=1
    )

    await change.execute(client, SANDBOX, TOKEN)

    assert (client.calls[0].method, client.calls[0].text_body) == ("PUT", zone)
    assert change.subject() != other.subject()


async def test_a_snapshot_restore_reads_the_snapshot_and_replaces_the_zone() -> None:
    zone_data: list[JsonValue] = [
        {"rrset_name": "@", "rrset_type": "A", "rrset_values": ["192.0.2.1"]}
    ]
    snapshot = GandiResponse(200, {"id": "snap-1", "name": "before", "zone_data": zone_data})
    client = FakeGandiClient(
        [
            details(automatic=True),
            GandiResponse(200, [], total_count=5),
            snapshot,
            snapshot,
            GandiResponse(201, None),
        ]
    )
    restore = SnapshotRestore(DOMAIN, SnapshotId("snap-1"))

    await restore.prepare(client, SANDBOX, TOKEN)
    await restore.execute(client, SANDBOX, TOKEN, ConfirmationAnswer())

    assert restore.describe().params == {
        "domain": "example.com",
        "snapshot": "before",
        "count": 5,
        "new": 1,
    }
    assert client.calls[-1].path == (*ZONE, "records")
    assert client.calls[-1].body == {"items": zone_data}
    assert "snap-1" in restore.subject()


async def test_a_snapshot_without_records_is_refused() -> None:
    client = FakeGandiClient([GandiResponse(200, {"id": "snap-1"})])

    with pytest.raises(Exception, match="no records"):
        await SnapshotRestore(DOMAIN, SnapshotId("snap-1")).execute(client, SANDBOX, TOKEN)

    assert [call.method for call in client.calls] == ["GET"]
