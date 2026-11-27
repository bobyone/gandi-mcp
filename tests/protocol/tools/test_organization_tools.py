# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the organization tools."""

import json
from typing import Any

import mcp_types as types
import pytest
from mcp.client import Client

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.gandi.gandi_organization_directory import GandiOrganizationDirectory
from gandi_mcp.accounts.organization_service import OrganizationService
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.content.long_text_filter import LongTextFilter
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.protocol.error_presenter import (
    INVALID_ORGANIZATION,
    UNKNOWN_ORGANIZATION,
    ErrorPresenter,
)
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.organization_tools import OrganizationTools
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.fake_gandi_client import FakeGandiClient
from tests.doubles.fake_token_entry_page import FakeTokenEntryPage
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.source_translator import SourceTranslator
from tests.doubles.stub_token_verifier import StubTokenVerifier

ORG_ID = "5a53edc7-b514-416a-98c2-2d477a288eb9"
OTHER_ID = "0b1c2d3e-4f50-4617-8899-aabbccddeeff"
pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
ORGANIZATIONS: JsonValue = [
    {
        "id": ORG_ID,
        "name": "Ada Corp",
        "type": "company",
        "email": "a@b.org",
    }
]


async def server(read_only: bool = False) -> tuple[Any, FakeGandiClient]:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    draft = AccountDraft(AccountName("Perso"), Environment.SANDBOX, read_only=read_only)
    await accounts.add(draft, TOKEN)
    translator, presenter = SourceTranslator(), LinkPresenter(FakeBrowser())
    pending = PendingConfirmations(300)
    tools = AccountsTools(
        accounts,
        ConfirmationService(
            [LocalLinkChannel(pending, FakeConfirmationPage(), presenter, translator)], pending
        ),
        TokenEntryService(TokenEntrySessions(600), FakeTokenEntryPage(), presenter, translator),
        ErrorPresenter(translator, LongTextFilter(280)),
        translator,
    )
    gandi = FakeGandiClient()
    service = OrganizationService(accounts, secrets, GandiOrganizationDirectory(gandi))
    return create_server("1.0.0", [OrganizationTools(service, tools)]), gandi


def content(result: types.CallToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: types.CallToolResult) -> str:
    assert result.is_error
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    return block.text


async def test_tools_and_annotations() -> None:
    mcp_server, _gandi = await server()
    async with Client(mcp_server) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    assert set(tools) == {"list_organizations", "set_paying_organization"}
    listing = tools["list_organizations"].annotations
    choosing = tools["set_paying_organization"].annotations
    assert listing is not None
    assert listing.read_only_hint
    assert choosing is not None
    assert not choosing.read_only_hint
    assert not choosing.destructive_hint


async def test_list_then_choose_the_paying_organization() -> None:
    mcp_server, gandi = await server(read_only=True)
    gandi.outcomes.extend([GandiResponse(200, ORGANIZATIONS), GandiResponse(200, ORGANIZATIONS)])

    async with Client(mcp_server) as session:
        listed = content(await session.call_tool("list_organizations", {}))
        chosen = content(
            await session.call_tool(
                "set_paying_organization",
                {"organization_id": ORG_ID},
            )
        )
        cleared = content(await session.call_tool("set_paying_organization", {}))

    assert listed["untrusted_data"] == [{"id": ORG_ID, "name": "Ada Corp", "type": "company"}]
    assert "a@b.org" not in json.dumps(listed)
    assert chosen["account"]["paying_organization"] == ORG_ID
    assert cleared["account"]["paying_organization"] is None


async def test_errors_are_explained() -> None:
    mcp_server, gandi = await server()
    gandi.outcomes.append(GandiResponse(200, ORGANIZATIONS))

    async with Client(mcp_server) as session:
        invalid = error_text(
            await session.call_tool("set_paying_organization", {"organization_id": "x"})
        )
        unknown = error_text(
            await session.call_tool(
                "set_paying_organization",
                {"organization_id": OTHER_ID},
            )
        )

    assert invalid.endswith(INVALID_ORGANIZATION.singular)
    assert unknown.endswith(UNKNOWN_ORGANIZATION.singular)
