# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the order tools, from the quote to the order."""

import json
from dataclasses import dataclass
from typing import Any

import mcp_types as types
import pytest
from mcp.client import Client

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.content.long_text_filter import LongTextFilter
from gandi_mcp.domains.contacts.contact_redactor import ContactRedactor
from gandi_mcp.domains.quotes.gandi.gandi_quote_provider import GandiQuoteProvider
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.operations.order_executor import OrderExecutor
from gandi_mcp.protocol.error_presenter import INVALID_CONTACT, NOT_AVAILABLE, ErrorPresenter
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.domains.domain_order_runner import DomainOrderRunner
from gandi_mcp.protocol.tools.domains.order_tools import OrderTools
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue
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

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
OWNER = {
    "type": "individual",
    "given": "Ada",
    "family": "Lovelace",
    "email": "ada@example.org",
    "streetaddr": "1 rue de Paris",
    "city": "Paris",
    "zip": "75001",
    "country": "FR",
}


def check(process: str, status: str = "available") -> GandiResponse:
    data: JsonValue = {
        "currency": "EUR",
        "products": [
            {
                "status": status,
                "process": process,
                "prices": [
                    {
                        "min_duration": 1,
                        "max_duration": 10,
                        "price_after_taxes": 12.0,
                        "price_before_taxes": 10.0,
                    }
                ],
            }
        ],
    }
    return GandiResponse(200, data)


@dataclass
class Setup:
    server: Any
    gandi: FakeGandiClient
    pending: PendingConfirmations
    accounts: AccountService


@pytest.fixture
async def setup() -> Setup:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    translator, presenter = SourceTranslator(), LinkPresenter(FakeBrowser())
    pending = PendingConfirmations(300)
    confirmation = ConfirmationService(
        [LocalLinkChannel(pending, FakeConfirmationPage(), presenter, translator)], pending
    )
    tools = AccountsTools(
        accounts,
        confirmation,
        TokenEntryService(TokenEntrySessions(600), FakeTokenEntryPage(), presenter, translator),
        ErrorPresenter(translator, LongTextFilter(280)),
        translator,
    )
    gandi = FakeGandiClient()
    orders = OrderExecutor(
        accounts,
        secrets,
        gandi,
        confirmation,
        quotes=GandiQuoteProvider(gandi),
        translator=translator,
    )
    runner = DomainOrderRunner(orders, tools, ContactRedactor(), LongTextFilter(280))
    return Setup(create_server("1.0.0", [OrderTools(runner)]), gandi, pending, accounts)


def data(result: types.CallToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: types.CallToolResult) -> str:
    assert result.is_error
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    return block.text


async def test_tools_and_annotations(setup: Setup) -> None:
    async with Client(setup.server) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    assert set(tools) == {"domain_register", "domain_renew", "domain_restore", "domain_transfer_in"}
    for tool in tools.values():
        assert tool.annotations is not None
        assert not tool.annotations.read_only_hint
        assert not tool.annotations.idempotent_hint
        assert "authinfo" not in json.dumps(tool.input_schema)
        assert "confirmation_id" in tool.input_schema["properties"]


async def test_register_from_quote_to_order(setup: Setup) -> None:
    setup.gandi.outcomes.extend(
        [
            check("create"),
            GandiResponse(200, {"status": "success"}),
            check("create"),
            check("create"),
            GandiResponse(202, {"message": "Confirmation"}),
        ]
    )
    arguments = {"domain": "example.com", "duration": 2, "owner": OWNER}

    async with Client(setup.server) as session:
        first = data(await session.call_tool("domain_register", arguments))
        setup.pending.answer(first["confirmation_id"], True)
        second = data(
            await session.call_tool(
                "domain_register", {**arguments, "confirmation_id": first["confirmation_id"]}
            )
        )

    assert first["status"] == "confirmation_pending"
    assert second["status"] == "ordered"
    assert "domain_creation_status" in second["next_step"]
    order = setup.gandi.calls[-1]
    assert (order.method, order.path, order.dry_run) == ("POST", ("domain", "domains"), False)
    assert isinstance(order.body, dict)
    assert order.body["price"] == 20.0


async def test_transfer_code_never_goes_through_the_model(setup: Setup) -> None:
    setup.gandi.outcomes.extend([check("transfer"), check("transfer"), check("transfer")])
    arguments = {"domain": "example.com", "duration": 1, "owner": OWNER}

    async with Client(setup.server) as session:
        first = data(await session.call_tool("domain_transfer_in", arguments))
        setup.pending.answer(first["confirmation_id"], True, SecretValue("Auth-123"))
        second = data(
            await session.call_tool(
                "domain_transfer_in", {**arguments, "confirmation_id": first["confirmation_id"]}
            )
        )

    assert "Auth-123" not in json.dumps([first, second])
    body = setup.gandi.calls[-1].body
    assert isinstance(body, dict)
    assert body["authinfo"] == "Auth-123"


async def test_errors_are_explained(setup: Setup) -> None:
    setup.gandi.outcomes.append(check("create", "unavailable"))

    async with Client(setup.server) as session:
        taken = error_text(
            await session.call_tool(
                "domain_register", {"domain": "example.com", "duration": 1, "owner": OWNER}
            )
        )
        bad_contact = error_text(
            await session.call_tool(
                "domain_register",
                {"domain": "example.com", "duration": 1, "owner": {**OWNER, "email": "x@y"}},
            )
        )

    assert taken.endswith(NOT_AVAILABLE.singular)
    assert bad_contact.endswith(INVALID_CONTACT.singular)


async def test_renew_and_restore_on_a_read_only_account_are_refused(setup: Setup) -> None:
    await setup.accounts.update(AccountName("Perso"), read_only=True)

    async with Client(setup.server) as session:
        renew = await session.call_tool("domain_renew", {"domain": "example.com", "duration": 1})
        restore = await session.call_tool("domain_restore", {"domain": "example.com"})

    assert renew.is_error
    assert restore.is_error
    assert setup.gandi.calls == []
