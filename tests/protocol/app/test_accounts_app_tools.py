# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the MCP App tools, with an in-memory client declaring MCP Apps."""

from dataclasses import dataclass
from typing import Any

import mcp_types as types
import pytest
from mcp.client import Client
from mcp.client.extension import ClientExtension
from mcp.client.session import ClientRequestContext
from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.protocol.app.accounts_app_tools import AccountsAppTools
from gandi_mcp.protocol.app.app_resource import APP_URI
from gandi_mcp.protocol.error_presenter import ErrorPresenter
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.fake_token_entry_page import FakeTokenEntryPage
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.source_translator import SourceTranslator
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
PRODUCTION = PersonalAccessToken("pat_production_01234567")
HTML = "<!doctype html><title>Gandi</title>"
APP_TOOLS = {
    "app_list_accounts",
    "app_add_account",
    "app_update_account",
    "app_replace_account_token",
    "app_change_account_environment",
    "app_remove_account",
}


class McpAppsSupport(ClientExtension):
    """Declare the MCP Apps extension, as a host rendering the App does."""

    identifier = EXTENSION_ID

    def settings(self) -> dict[str, Any]:
        return {"mimeTypes": [APP_MIME_TYPE]}


@dataclass
class Setup:
    accounts: AccountService
    secrets: InMemorySecretStore
    server_tools: AccountsTools
    app_tools: AccountsAppTools
    pending: PendingConfirmations
    browser: FakeBrowser


@pytest.fixture
def setup() -> Setup:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    verifier.accept(Environment.PRODUCTION, PRODUCTION)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    translator, browser = SourceTranslator(), FakeBrowser()
    pending, presenter = PendingConfirmations(300), LinkPresenter(browser)
    confirmation = ConfirmationService(
        [
            ElicitationChannel(translator),
            LocalLinkChannel(pending, FakeConfirmationPage(), presenter, translator),
        ],
        pending,
    )
    tools = AccountsTools(
        accounts,
        confirmation,
        TokenEntryService(TokenEntrySessions(600), FakeTokenEntryPage(), presenter, translator),
        ErrorPresenter(translator),
        translator,
    )
    app_tools = AccountsAppTools(accounts, tools, translator, HTML)
    return Setup(accounts, secrets, tools, app_tools, pending, browser)


async def accept(
    context: ClientRequestContext, params: types.ElicitRequestParams
) -> types.ElicitResult | types.ErrorData:
    """A user accepting every elicitation."""
    return types.ElicitResult(action="accept", content={"confirm": True})


def client(setup: Setup, apps: bool = True, elicitation: bool = False) -> Client:
    server = create_server("1.0.0", [setup.server_tools], app_modules=[setup.app_tools])
    extensions = [McpAppsSupport()] if apps else []
    if elicitation:
        return Client(server, extensions=extensions, elicitation_callback=accept, mode="legacy")
    return Client(server, extensions=extensions)


def data(result: types.CallToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: types.CallToolResult) -> str:
    assert result.is_error
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    return block.text


async def test_tools_are_bound_to_the_app_with_their_visibility(setup: Setup) -> None:
    async with client(setup) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    assert APP_TOOLS | {"open_gandi_app"} <= set(tools)
    for name in APP_TOOLS:
        ui = (tools[name].meta or {})["ui"]
        assert ui == {"resourceUri": APP_URI, "visibility": ["app"]}
    assert (tools["open_gandi_app"].meta or {})["ui"]["visibility"] == ["model", "app"]
    assert tools["app_remove_account"].annotations.destructive_hint  # type: ignore[union-attr]
    for name in (
        set(tools)
        - {"app_add_account", "app_replace_account_token"}
        - {"app_change_account_environment"}
    ):
        assert "token" not in tools[name].input_schema.get("properties", {})


async def test_the_app_resource_is_served(setup: Setup) -> None:
    async with client(setup) as session:
        resource = await session.read_resource(APP_URI)

    content = resource.contents[0]
    assert isinstance(content, types.TextResourceContents)
    assert content.mime_type == APP_MIME_TYPE
    assert content.text == HTML
    assert (content.meta or {})["ui"]["csp"] == {}


async def test_app_tools_are_refused_without_mcp_apps(setup: Setup) -> None:
    async with client(setup, apps=False) as session:
        listed = await session.call_tool("app_list_accounts", {})
        added = await session.call_tool(
            "app_add_account", {"name": "Perso", "environment": "sandbox", "token": TOKEN.reveal()}
        )
        opened = data(await session.call_tool("open_gandi_app", {}))

    assert "only be used from the Gandi app" in error_text(listed)
    assert "only be used from the Gandi app" in error_text(added)
    assert await setup.accounts.list() == ()
    assert opened == {"accounts": []}


async def test_add_list_and_manage_accounts_from_the_app(setup: Setup) -> None:
    async with client(setup) as session:
        added = data(
            await session.call_tool(
                "app_add_account",
                {"name": "Perso", "environment": "sandbox", "token": TOKEN.reveal()},
            )
        )
        locked = data(
            await session.call_tool("app_update_account", {"name": "Perso", "read_only": True})
        )
        listed = data(await session.call_tool("app_list_accounts", {}))

    assert added == {
        "account": {
            "name": "Perso",
            "environment": "sandbox",
            "read_only": False,
            "is_default": True,
            "removal_pending": False,
        },
        "username": "ada",
    }
    assert TOKEN.reveal() not in str(added)
    assert locked["account"]["read_only"]
    assert [account["name"] for account in listed["accounts"]] == ["Perso"]


async def test_an_app_call_alone_never_confirms(setup: Setup) -> None:
    """Advertising MCP Apps is no proof of a click: the user still confirms."""
    await setup.accounts.add(
        AccountDraft(AccountName("Perso"), Environment.SANDBOX, read_only=True), TOKEN
    )

    async with client(setup) as session:
        unlock = data(
            await session.call_tool("app_update_account", {"name": "Perso", "read_only": False})
        )
        remove = data(await session.call_tool("app_remove_account", {"name": "Perso"}))

    assert unlock["status"] == remove["status"] == "confirmation_pending"
    assert len(setup.browser.opened) == 2
    account = await setup.accounts.resolve()
    assert account.read_only
    assert len(setup.secrets.tokens) == 1


async def test_app_changes_resume_once_confirmed_on_the_page(setup: Setup) -> None:
    await setup.accounts.add(
        AccountDraft(AccountName("Perso"), Environment.SANDBOX, read_only=True), TOKEN
    )

    async with client(setup) as session:
        unlock = data(
            await session.call_tool("app_update_account", {"name": "Perso", "read_only": False})
        )
        setup.pending.answer(unlock["confirmation_id"], True)
        unlocked = data(
            await session.call_tool(
                "app_update_account",
                {"name": "Perso", "read_only": False, "confirmation_id": unlock["confirmation_id"]},
            )
        )
        remove = data(await session.call_tool("app_remove_account", {"name": "Perso"}))
        setup.pending.answer(remove["confirmation_id"], True)
        removed = data(
            await session.call_tool(
                "app_remove_account",
                {"name": "Perso", "confirmation_id": remove["confirmation_id"]},
            )
        )

    assert not unlocked["account"]["read_only"]
    assert removed["status"] == "removed"
    assert setup.secrets.tokens == {}


async def test_tokens_are_checked_and_replaced(setup: Setup) -> None:
    await setup.accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    key = (await setup.accounts.resolve()).secret_key

    async with client(setup) as session:
        invalid = await session.call_tool(
            "app_replace_account_token", {"name": "Perso", "token": "short"}
        )
        rejected = await session.call_tool(
            "app_replace_account_token", {"name": "Perso", "token": PRODUCTION.reveal()}
        )
        moved = data(
            await session.call_tool(
                "app_change_account_environment",
                {"name": "Perso", "environment": "production", "token": PRODUCTION.reveal()},
            )
        )

    assert "not a valid Personal Access Token" in error_text(invalid)
    assert "short" not in error_text(invalid)
    assert "Gandi refused the token" in error_text(rejected)
    assert PRODUCTION.reveal() not in error_text(rejected)
    assert moved["account"]["environment"] == "production"
    assert setup.secrets.tokens[key] == PRODUCTION


async def test_remove_from_the_app_with_elicitation(setup: Setup) -> None:
    await setup.accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)

    async with client(setup, elicitation=True) as session:
        removed = data(await session.call_tool("app_remove_account", {"name": "Perso"}))

    assert removed["status"] == "removed"
    assert setup.browser.opened == []
    assert setup.secrets.tokens == {}
