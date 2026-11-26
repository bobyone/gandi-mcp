# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the account tools, with an in-memory MCP client and doubles."""

import json
from dataclasses import dataclass, field
from typing import Any

import mcp_types as types
import pytest
from mcp.client import Client
from mcp.client.session import ClientRequestContext

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.channels.app_channel import AppChannel
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.protocol.error_presenter import ErrorPresenter
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_entry_target import TokenPurpose
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.fake_token_entry_page import FakeTokenEntryPage
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.source_translator import SourceTranslator
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")


@dataclass
class User:
    """Answers the elicitations of the client like a user would."""

    accept: bool = True
    forms: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)

    async def __call__(
        self, context: ClientRequestContext, params: types.ElicitRequestParams
    ) -> types.ElicitResult | types.ErrorData:
        if isinstance(params, types.ElicitRequestURLParams):
            self.links.append(params.url)
            return types.ElicitResult(action="accept" if self.accept else "decline")
        self.forms.append(params.message)
        if not self.accept:
            return types.ElicitResult(action="decline")
        return types.ElicitResult(action="accept", content={"confirm": True})


@dataclass
class Setup:
    tools: AccountsTools
    accounts: AccountService
    secrets: InMemorySecretStore
    sessions: TokenEntrySessions
    token_page: FakeTokenEntryPage
    pending: PendingConfirmations
    browser: FakeBrowser


@pytest.fixture
def setup() -> Setup:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    translator, browser = SourceTranslator(), FakeBrowser()
    presenter = LinkPresenter(browser)
    pending, sessions = PendingConfirmations(300), TokenEntrySessions(600)
    token_page = FakeTokenEntryPage()
    confirmation = ConfirmationService(
        [
            AppChannel(),
            ElicitationChannel(translator),
            LocalLinkChannel(pending, FakeConfirmationPage(), presenter, translator),
        ],
        pending,
    )
    tools = AccountsTools(
        accounts,
        confirmation,
        TokenEntryService(sessions, token_page, presenter, translator),
        ErrorPresenter(translator),
        translator,
    )
    return Setup(tools, accounts, secrets, sessions, token_page, pending, browser)


def client(setup: Setup, user: User | None = None) -> Client:
    """A client with elicitation on the 2025-11-25 protocol, otherwise the latest one."""
    server = create_server("1.0.0", [setup.tools])
    if user is None:
        return Client(server)
    return Client(server, elicitation_callback=user, mode="legacy")


def data(result: types.CallToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: types.CallToolResult) -> str:
    assert result.is_error
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    return block.text


async def add(setup: Setup, *names: str) -> None:
    for name in names:
        await setup.accounts.add(AccountDraft(AccountName(name), Environment.SANDBOX), TOKEN)


async def test_tools_and_annotations(setup: Setup) -> None:
    async with client(setup) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    assert set(tools) == {
        "list_accounts",
        "add_account",
        "update_account",
        "replace_account_token",
        "change_account_environment",
        "remove_account",
    }
    annotations = {name: tool.annotations for name, tool in tools.items()}
    assert all(item is not None for item in annotations.values())
    assert annotations["list_accounts"].read_only_hint  # type: ignore[union-attr]
    assert annotations["remove_account"].destructive_hint  # type: ignore[union-attr]
    for tool in tools.values():
        assert "token" not in tool.input_schema.get("properties", {})


async def test_list_accounts_never_shows_secrets(setup: Setup) -> None:
    await add(setup, "Perso", "Pro")

    async with client(setup) as session:
        result = data(await session.call_tool("list_accounts", {}))

    assert result == {
        "accounts": [
            {"name": "Perso", "environment": "sandbox", "read_only": False, "is_default": True},
            {"name": "Pro", "environment": "sandbox", "read_only": False, "is_default": False},
        ]
    }
    text = json.dumps(result)
    assert TOKEN.reveal() not in text
    assert all(key not in text for key in setup.secrets.tokens)


async def test_add_account_opens_the_browser_without_elicitation(setup: Setup) -> None:
    async with client(setup) as session:
        result = data(
            await session.call_tool(
                "add_account", {"name": "Perso", "environment": "sandbox", "read_only": True}
            )
        )

    assert result["status"] == "token_entry_page_shown"
    assert setup.browser.opened
    assert "http" not in json.dumps(result)
    target = setup.token_page.opened[0].target
    assert (target.purpose, str(target.name), target.read_only) == (
        TokenPurpose.ADD,
        "Perso",
        True,
    )


async def test_add_account_through_url_elicitation(setup: Setup) -> None:
    user = User()

    async with client(setup, user) as session:
        result = data(
            await session.call_tool("add_account", {"name": "Perso", "environment": "production"})
        )

    assert user.links == [f"http://127.0.0.1:1/token/{setup.token_page.opened[0].session_id}"]
    assert setup.browser.opened == []
    assert user.links[0] not in json.dumps(result)


async def test_add_account_refuses_a_used_or_invalid_name(setup: Setup) -> None:
    await add(setup, "Perso")

    async with client(setup) as session:
        duplicate = await session.call_tool(
            "add_account", {"name": "PERSO", "environment": "sandbox"}
        )
        invalid = await session.call_tool(
            "add_account", {"name": "bad_name", "environment": "sandbox"}
        )

    assert "choose another name" in error_text(duplicate)
    assert "not valid" in error_text(invalid)
    assert setup.token_page.opened == []


async def test_add_account_when_no_browser_opens(setup: Setup) -> None:
    setup.browser.available = False

    async with client(setup) as session:
        result = await session.call_tool("add_account", {"name": "Perso", "environment": "sandbox"})

    assert "could not be opened" in error_text(result)


async def test_replace_token_and_change_environment_open_pages(setup: Setup) -> None:
    await add(setup, "Perso")

    async with client(setup) as session:
        data(await session.call_tool("replace_account_token", {"name": "perso"}))
        data(
            await session.call_tool(
                "change_account_environment", {"name": "Perso", "environment": "production"}
            )
        )
        missing = await session.call_tool("replace_account_token", {"name": "Nope"})

    purposes = [(s.target.purpose, s.target.environment) for s in setup.token_page.opened]
    assert purposes == [
        (TokenPurpose.REPLACE, Environment.SANDBOX),
        (TokenPurpose.CHANGE_ENVIRONMENT, Environment.PRODUCTION),
    ]
    assert "No account has this name" in error_text(missing)


async def test_update_account(setup: Setup) -> None:
    await add(setup, "Perso", "Pro")

    async with client(setup) as session:
        renamed = data(
            await session.call_tool(
                "update_account", {"name": "Pro", "new_name": "Work", "make_default": True}
            )
        )
        locked = data(
            await session.call_tool("update_account", {"name": "Work", "read_only": True})
        )
        unchanged = data(await session.call_tool("update_account", {"name": "Perso"}))

    assert renamed["account"] == {
        "name": "Work",
        "environment": "sandbox",
        "read_only": False,
        "is_default": True,
    }
    assert locked["account"]["read_only"]
    assert unchanged["account"]["name"] == "Perso"


async def test_allowing_writes_needs_a_confirmation(setup: Setup) -> None:
    await setup.accounts.add(
        AccountDraft(AccountName("Watch"), Environment.SANDBOX, read_only=True), TOKEN
    )
    refusing, accepting = User(accept=False), User()

    async with client(setup, refusing) as session:
        refused = await session.call_tool("update_account", {"name": "Watch", "read_only": False})
    async with client(setup, accepting) as session:
        allowed = data(
            await session.call_tool("update_account", {"name": "Watch", "read_only": False})
        )

    assert "refused" in error_text(refused)
    assert refusing.forms == [
        "Confirm on the sandbox account Watch: allow write operations on the account Watch"
    ]
    assert not allowed["account"]["read_only"]


async def test_remove_account_with_elicitation(setup: Setup) -> None:
    await add(setup, "Perso", "Beta")

    async with client(setup, User()) as session:
        result = data(await session.call_tool("remove_account", {"name": "Perso"}))

    assert result == {
        "status": "removed",
        "account": "Perso",
        "new_default_account": "Beta",
    }


async def test_remove_account_refused(setup: Setup) -> None:
    await add(setup, "Perso")

    async with client(setup, User(accept=False)) as session:
        result = await session.call_tool("remove_account", {"name": "Perso"})

    assert "refused" in error_text(result)
    assert len(await setup.accounts.list()) == 1


async def test_remove_account_through_a_local_page(setup: Setup) -> None:
    await add(setup, "Perso")

    async with client(setup) as session:
        first = data(await session.call_tool("remove_account", {"name": "Perso"}))
        confirmation_id = first["confirmation_id"]
        waiting = data(
            await session.call_tool(
                "remove_account", {"name": "Perso", "confirmation_id": confirmation_id}
            )
        )
        setup.pending.answer(confirmation_id, True)
        done = data(
            await session.call_tool(
                "remove_account", {"name": "Perso", "confirmation_id": confirmation_id}
            )
        )

    assert first["status"] == waiting["status"] == "confirmation_pending"
    assert "http" not in json.dumps(first)
    assert setup.browser.opened
    assert done["status"] == "removed"


async def test_invented_or_reused_confirmation_is_refused(setup: Setup) -> None:
    await add(setup, "Perso", "Pro")

    async with client(setup) as session:
        invented = await session.call_tool(
            "remove_account", {"name": "Perso", "confirmation_id": "invented"}
        )
        first = data(await session.call_tool("remove_account", {"name": "Perso"}))
        setup.pending.answer(first["confirmation_id"], True)
        other = await session.call_tool(
            "remove_account", {"name": "Pro", "confirmation_id": first["confirmation_id"]}
        )

    assert "unknown, already used or for another operation" in error_text(invented)
    assert "for another operation" in error_text(other)
    assert len(await setup.accounts.list()) == 2


async def test_latest_protocol_falls_back_to_the_local_page(setup: Setup) -> None:
    await add(setup, "Perso")
    user = User()
    server = create_server("1.0.0", [setup.tools])

    async with Client(server, elicitation_callback=user) as session:
        result = data(await session.call_tool("remove_account", {"name": "Perso"}))

    assert result["status"] == "confirmation_pending"
    assert user.forms == []
    assert setup.browser.opened


async def test_errors_without_account(setup: Setup) -> None:
    async with client(setup, User()) as session:
        result = await session.call_tool("remove_account", {"name": "Perso"})

    assert "No Gandi account is configured" in error_text(result)


async def test_a_confirmation_does_not_apply_to_a_replaced_account(setup: Setup) -> None:
    await add(setup, "Perso")

    async with client(setup) as session:
        first = data(await session.call_tool("remove_account", {"name": "Perso"}))
        setup.pending.answer(first["confirmation_id"], True)
        await setup.accounts.remove(AccountName("Perso"))
        await add(setup, "Perso")
        resumed = await session.call_tool(
            "remove_account", {"name": "Perso", "confirmation_id": first["confirmation_id"]}
        )

    assert "for another operation" in error_text(resumed)
    assert len(await setup.accounts.list()) == 1


async def test_token_pages_are_bound_to_the_account_shown(setup: Setup) -> None:
    await add(setup, "Perso")
    reference = (await setup.accounts.resolve()).reference

    async with client(setup) as session:
        data(await session.call_tool("replace_account_token", {"name": "Perso"}))
        data(
            await session.call_tool(
                "change_account_environment", {"name": "Perso", "environment": "production"}
            )
        )

    assert [s.target.expected for s in setup.token_page.opened] == [reference, reference]
