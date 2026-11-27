# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the export of a read text to the work directory, with doubles."""

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.files.exceptions import FileExistsInWorkDirectoryError
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.text_file_exporter import TextFileExporter
from gandi_mcp.protocol.tools.livedns.zone_transfer_tools import configuration
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.in_memory_work_directory import InMemoryWorkDirectory
from tests.doubles.scripted_operation import ScriptedOperation
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")


async def exporter_with(
    client: FakeGandiClient, directory: InMemoryWorkDirectory
) -> TextFileExporter:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    confirmation = ConfirmationService([], PendingConfirmations(300))
    return TextFileExporter(OperationExecutor(accounts, secrets, client, confirmation), directory)


def read() -> ScriptedOperation:
    return ScriptedOperation(OperationCategory.READ, method="GET")


async def test_writes_the_text_read_by_the_operation() -> None:
    client = FakeGandiClient([GandiResponse(200, "@ 300 IN A 192.0.2.1\n")])
    directory = InMemoryWorkDirectory()
    exporter = await exporter_with(client, directory)

    written, text = await exporter.export(read(), None, ConfirmationContext(), "zone.txt")

    assert directory.files == {"zone.txt": "@ 300 IN A 192.0.2.1\n"}
    assert text == "@ 300 IN A 192.0.2.1\n"
    assert (written.relative_path, written.size) == ("zone.txt", 21)
    assert not directory.private


async def test_an_existing_file_is_refused_before_asking_gandi() -> None:
    client = FakeGandiClient()
    directory = InMemoryWorkDirectory({"zone.txt": "old"})
    exporter = await exporter_with(client, directory)

    with pytest.raises(FileExistsInWorkDirectoryError):
        await exporter.export(read(), None, ConfirmationContext(), "zone.txt")

    assert not client.calls
    assert directory.files == {"zone.txt": "old"}


async def test_an_extracted_private_text_replaces_an_existing_file_when_asked() -> None:
    client = FakeGandiClient([GandiResponse(200, {"configuration": "key secret;"})])
    directory = InMemoryWorkDirectory({"bind.conf": "old"})
    exporter = await exporter_with(client, directory)

    await exporter.export(
        read(),
        AccountName("Perso"),
        ConfirmationContext(),
        "bind.conf",
        overwrite=True,
        extract=configuration,
        private=True,
    )

    assert directory.files == {"bind.conf": "key secret;"}
    assert directory.private == {"bind.conf"}


async def test_no_text_means_nothing_is_written() -> None:
    client = FakeGandiClient([GandiResponse(200, {"not": "text"})])
    directory = InMemoryWorkDirectory()
    exporter = await exporter_with(client, directory)

    with pytest.raises(GandiUnexpectedResponseError):
        await exporter.export(read(), None, ConfirmationContext(), "zone.txt")

    assert not directory.files


async def test_a_write_operation_is_never_exported() -> None:
    client = FakeGandiClient()
    exporter = await exporter_with(client, InMemoryWorkDirectory())

    with pytest.raises(TypeError):
        await exporter.export(
            ScriptedOperation(OperationCategory.WRITE), None, ConfirmationContext(), "zone.txt"
        )

    assert not client.calls
