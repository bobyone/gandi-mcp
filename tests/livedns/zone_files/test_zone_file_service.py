# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the zone file export, with doubles."""

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.gandi.media_type import MediaType
from gandi_mcp.livedns.identifiers import SnapshotId
from gandi_mcp.livedns.zone_files.zone_file_service import ZoneFileService
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.text_file_exporter import TextFileExporter
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.in_memory_work_directory import InMemoryWorkDirectory
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
ZONE = "$TTL 300\n@ 300 IN A 192.0.2.1\nwww 300 IN CNAME @\n"


async def service_with(
    client: FakeGandiClient, directory: InMemoryWorkDirectory
) -> ZoneFileService:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    executor = OperationExecutor(
        accounts, secrets, client, ConfirmationService([], PendingConfirmations(300))
    )
    return ZoneFileService(TextFileExporter(executor, directory))


async def test_exports_the_zone_as_a_zone_file() -> None:
    client = FakeGandiClient([GandiResponse(200, ZONE)])
    directory = InMemoryWorkDirectory()
    service = await service_with(client, directory)

    export = await service.export(
        None, ConfirmationContext(), DomainName("Bücher.de"), "zones/bucher.zone"
    )

    call = client.calls[0]
    assert call.path == ("livedns", "domains", "xn--bcher-kva.de", "records")
    assert call.accept is MediaType.TEXT
    assert directory.files == {"zones/bucher.zone": ZONE}
    assert export.record_count == 2
    assert export.file.relative_path == "zones/bucher.zone"


async def test_exports_a_snapshot_as_a_zone_file() -> None:
    client = FakeGandiClient([GandiResponse(200, ZONE)])
    directory = InMemoryWorkDirectory()
    service = await service_with(client, directory)

    await service.export(
        AccountName("Perso"),
        ConfirmationContext(),
        DomainName("example.com"),
        "snapshot.zone",
        snapshot=SnapshotId("snap-1"),
    )

    assert client.calls[0].path == ("livedns", "domains", "example.com", "snapshots", "snap-1")
    assert client.calls[0].accept is MediaType.TEXT
