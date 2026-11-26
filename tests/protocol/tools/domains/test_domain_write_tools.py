# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Protocol tests of the domain write tools: requests, confirmations, secrets, dry runs."""

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
from gandi_mcp.gandi.exceptions import GandiValidationError
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.protocol.error_presenter import (
    DRY_RUN_REJECTED,
    INVALID_DOMAIN_INPUT,
    READ_ONLY,
    ErrorPresenter,
)
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.domains.contact_tools import ContactTools
from gandi_mcp.protocol.tools.domains.domain_settings_tools import DomainSettingsTools
from gandi_mcp.protocol.tools.domains.domain_tool_runner import DomainToolRunner
from gandi_mcp.protocol.tools.domains.nameserver_write_tools import NameserverWriteTools
from gandi_mcp.protocol.tools.domains.redirection_write_tools import RedirectionWriteTools
from gandi_mcp.protocol.tools.domains.tag_tools import TagTools
from gandi_mcp.protocol.tools.domains.transfer_write_tools import TransferWriteTools
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
D = ("domain", "domains", "example.com")
CONTACT = {
    "type": "individual",
    "given": "Ada",
    "family": "Lovelace",
    "email": "ada@example.org",
    "streetaddr": "1 rue de Paris",
    "city": "Paris",
    "zip": "75001",
    "country": "FR",
}
CONTACT_JSON = {**CONTACT, "data_obfuscated": True, "mail_obfuscated": True}
KEY = {"algorithm": 13, "type": "zsk", "public_key": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="}
# Tool: (arguments, method, path, body).
CALLS: dict[str, tuple[dict[str, Any], str, tuple[str, ...], Any]] = {
    "domain_autorenew_update": (
        {
            "domain": "example.com",
            "enabled": True,
            "duration": 2,
            "organization_id": "5A53EDC7-B514-416A-98C2-2D477A288EB9",
        },
        "PATCH",
        (*D, "autorenew"),
        {"enabled": True, "duration": 2, "org_id": "5a53edc7-b514-416a-98c2-2d477a288eb9"},
    ),
    "domain_transfer_lock": (
        {"domain": "example.com"},
        "PATCH",
        (*D, "status"),
        {"clientTransferProhibited": True},
    ),
    "domain_transfer_unlock": (
        {"domain": "example.com"},
        "PATCH",
        (*D, "status"),
        {"clientTransferProhibited": False},
    ),
    "domain_authorization_code_reset": ({"domain": "example.com"}, "PUT", (*D, "authinfo"), None),
    "domain_reachability_resend": (
        {"domain": "example.com"},
        "PATCH",
        (*D, "reachability"),
        {"action": "resend"},
    ),
    "domain_claims_accept": ({"domain": "example.com"}, "POST", (*D, "claims"), None),
    "domain_delete": ({"domain": "example.com"}, "DELETE", D, None),
    "domain_contacts_update": (
        {"domain": "example.com", "tech": CONTACT},
        "PATCH",
        (*D, "contacts"),
        {"tech": CONTACT_JSON},
    ),
    "domain_owner_update": (
        {"domain": "example.com", "owner": CONTACT},
        "PUT",
        (*D, "contacts", "owner"),
        {key: value for key, value in CONTACT_JSON.items() if key != "type"},
    ),
    "domain_owner_email_update": (
        {"domain": "example.com", "owner": CONTACT},
        "PUT",
        (*D, "contacts", "owner"),
        {
            **{key: value for key, value in CONTACT_JSON.items() if key != "type"},
            "icann_contract_accept": True,
        },
    ),
    "domain_owner_change": (
        {"domain": "example.com", "owner": CONTACT},
        "POST",
        ("domain", "changeowner", "example.com"),
        {"owner": CONTACT_JSON},
    ),
    "domain_owner_change_resend": (
        {"domain": "example.com", "email": "a@example.org"},
        "POST",
        ("domain", "changeowner", "example.com", "foa"),
        {"email": "a@example.org"},
    ),
    "domain_nameservers_update": (
        {"domain": "example.com", "nameservers": ["NS1.example.net", "ns2.example.net"]},
        "PUT",
        (*D, "nameservers"),
        {"nameservers": ["ns1.example.net", "ns2.example.net"]},
    ),
    "domain_livedns_enable": ({"domain": "example.com"}, "POST", (*D, "livedns"), None),
    "domain_dnssec_enable": ({"domain": "example.com"}, "POST", (*D, "livedns", "dnssec"), None),
    "domain_dnssec_disable": ({"domain": "example.com"}, "DELETE", (*D, "livedns", "dnssec"), None),
    "domain_dnssec_key_add": ({"domain": "example.com", "key": KEY}, "POST", (*D, "dnskeys"), KEY),
    "domain_dnssec_keys_replace": (
        {"domain": "example.com", "keys": [KEY]},
        "PUT",
        (*D, "dnskeys"),
        {"keys": [KEY]},
    ),
    "domain_dnssec_key_delete": (
        {"domain": "example.com", "key_id": "42"},
        "DELETE",
        (*D, "dnskeys", "42"),
        None,
    ),
    "domain_glue_record_create": (
        {"domain": "example.com", "host": "NS1", "ips": ["203.0.113.2", "2001:db8::00ff"]},
        "POST",
        (*D, "hosts"),
        {"name": "ns1", "ips": ["203.0.113.2", "2001:db8::ff"]},
    ),
    "domain_glue_record_update": (
        {"domain": "example.com", "host": "ns1", "ips": ["203.0.113.3"]},
        "PUT",
        (*D, "hosts", "ns1"),
        {"ips": ["203.0.113.3"]},
    ),
    "domain_glue_record_delete": (
        {"domain": "example.com", "host": "ns1"},
        "DELETE",
        (*D, "hosts", "ns1"),
        None,
    ),
    "domain_web_redirection_create": (
        {"domain": "example.com", "host": "www.example.com", "url": "https://example.org/"},
        "POST",
        (*D, "webredirs"),
        {
            "host": "www.example.com",
            "url": "https://example.org/",
            "type": "http301",
            "protocol": "https",
            "override": False,
        },
    ),
    "domain_web_redirection_update": (
        {"domain": "example.com", "host": "www.example.com", "type": "http302"},
        "PATCH",
        (*D, "webredirs", "www.example.com"),
        {"type": "http302"},
    ),
    "domain_web_redirection_delete": (
        {"domain": "example.com", "host": "www.example.com"},
        "DELETE",
        (*D, "webredirs", "www.example.com"),
        None,
    ),
    "domain_tag_add": (
        {"domain": "example.com", "tag": " to renew "},
        "POST",
        (*D, "tags"),
        {"tag": "to renew"},
    ),
    "domain_tags_replace": (
        {"domain": "example.com", "tags": ["a", "b"]},
        "PUT",
        (*D, "tags"),
        {"tags": ["a", "b"]},
    ),
    "domain_tags_update": (
        {"domain": "example.com", "add": ["a"]},
        "PATCH",
        (*D, "tags"),
        {"add": ["a"], "remove": []},
    ),
    "domain_tags_delete": ({"domain": "example.com"}, "DELETE", (*D, "tags"), None),
    "domain_transfer_out_accept": (
        {"domain": "example.com"},
        "POST",
        (*D, "transferout"),
        {"accept": True, "authinfo": "Auth-123"},
    ),
    "domain_transfer_out_decline": (
        {"domain": "example.com"},
        "POST",
        (*D, "transferout"),
        {"accept": False, "authinfo": "Auth-123"},
    ),
    "domain_transfer_in_relaunch": (
        {"domain": "example.com"},
        "PUT",
        ("domain", "transferin", "example.com"),
        None,
    ),
    "domain_transfer_in_code_update": (
        {"domain": "example.com"},
        "PUT",
        ("domain", "transferin", "example.com", "authinfo"),
        {"authinfo": "Auth-123"},
    ),
    "domain_transfer_in_resend": (
        {"domain": "example.com", "email": "a@example.org"},
        "POST",
        ("domain", "transferin", "example.com", "foa"),
        {"email": "a@example.org"},
    ),
}
SECRET = {e.name for e in domain_endpoints.WRITE_ENDPOINTS if e.secret_field is not None}
CONFIRMED = {endpoint.name for endpoint in domain_endpoints.WRITE_ENDPOINTS if endpoint.confirmed}
DRY_RUN = {
    endpoint.name for endpoint in domain_endpoints.WRITE_ENDPOINTS if endpoint.supports_dry_run
}


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
    runner = DomainToolRunner(
        OperationExecutor(accounts, secrets, gandi, confirmation),
        tools,
        ContactRedactor(),
        LongTextFilter(280),
    )
    modules = [
        module(runner)
        for module in (
            DomainSettingsTools,
            ContactTools,
            NameserverWriteTools,
            RedirectionWriteTools,
            TagTools,
            TransferWriteTools,
        )
    ]
    return Setup(create_server("1.0.0", modules), gandi, pending, accounts)


def data(result: types.CallToolResult) -> dict[str, Any]:
    assert not result.is_error, result.content
    assert isinstance(result.structured_content, dict)
    return result.structured_content


def error_text(result: types.CallToolResult) -> str:
    assert result.is_error
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    return block.text


async def test_one_tool_per_write_endpoint_with_its_annotations(setup: Setup) -> None:
    async with Client(setup.server) as session:
        tools = {tool.name: tool for tool in (await session.list_tools()).tools}

    endpoints = {endpoint.name: endpoint for endpoint in domain_endpoints.WRITE_ENDPOINTS}
    assert set(tools) == set(endpoints) == set(CALLS)
    for name, tool in tools.items():
        annotations = tool.annotations
        assert annotations is not None
        assert not annotations.read_only_hint
        assert annotations.destructive_hint == endpoints[name].category.needs_confirmation
        assert ("confirmation_id" in tool.input_schema["properties"]) == (name in CONFIRMED)
        assert "authinfo" not in json.dumps(tool.input_schema)


@pytest.mark.parametrize("name", sorted(CALLS))
async def test_every_write_sends_its_request(setup: Setup, name: str) -> None:
    arguments, method, path, body = CALLS[name]
    if name in DRY_RUN:
        setup.gandi.outcomes.append(GandiResponse(200, {"status": "success"}))
    setup.gandi.outcomes.append(GandiResponse(202, {"message": "Accepted"}))

    async with Client(setup.server) as session:
        result = data(await session.call_tool(name, arguments))
        if name in CONFIRMED:
            assert result["status"] == "confirmation_pending"
            secret = SecretValue("Auth-123") if name in SECRET else None
            setup.pending.answer(result["confirmation_id"], True, secret)
            result = data(
                await session.call_tool(
                    name, {**arguments, "confirmation_id": result["confirmation_id"]}
                )
            )

    assert result["status"] == "done"
    call = setup.gandi.calls[-1]
    assert (call.method, call.path, call.body, call.dry_run) == (method, path, body, False)
    if name in DRY_RUN:
        assert setup.gandi.calls[0].dry_run
    assert "Auth-123" not in json.dumps(result)


async def test_a_rejected_dry_run_stops_the_owner_change(setup: Setup) -> None:
    setup.gandi.outcomes.append(
        GandiResponse(200, {"status": "error", "errors": [{"name": "owner", "description": "x"}]})
    )
    arguments, *_ = CALLS["domain_owner_change"]

    async with Client(setup.server) as session:
        text = error_text(await session.call_tool("domain_owner_change", arguments))

    assert DRY_RUN_REJECTED.singular.split(":")[0] in text or "refused" in text
    assert "- owner: x" in text
    assert len(setup.gandi.calls) == 1
    assert setup.pending._items == {}


async def test_invalid_inputs_are_refused_before_any_call(setup: Setup) -> None:
    async with Client(setup.server) as session:
        texts = [
            error_text(
                await session.call_tool(
                    "domain_glue_record_create",
                    {"domain": "example.com", "host": "ns1", "ips": ["999.1.1.1"]},
                )
            ),
            error_text(
                await session.call_tool(
                    "domain_web_redirection_create",
                    {"domain": "example.com", "host": "www.example.com", "url": "ftp://x.org/"},
                )
            ),
            error_text(
                await session.call_tool("domain_contacts_update", {"domain": "example.com"})
            ),
        ]

    assert all(text.endswith(INVALID_DOMAIN_INPUT.singular) for text in texts)
    assert setup.gandi.calls == []


async def test_writes_are_refused_on_a_read_only_account(setup: Setup) -> None:
    await setup.accounts.update(AccountName("Perso"), read_only=True)

    async with Client(setup.server) as session:
        text = error_text(
            await session.call_tool("domain_tag_add", {"domain": "example.com", "tag": "x"})
        )

    assert text.endswith(READ_ONLY.singular)
    assert setup.gandi.calls == []


@pytest.mark.parametrize(
    "outcome",
    [
        GandiResponse(200, {"message": "code Echo-123 accepted"}),
        GandiValidationError("refused", ("wrong code Echo-123",)),
    ],
)
async def test_a_typed_code_is_never_echoed_to_the_model(
    setup: Setup, outcome: GandiResponse | Exception
) -> None:
    setup.gandi.outcomes.append(outcome)

    async with Client(setup.server) as session:
        first = data(
            await session.call_tool("domain_transfer_in_code_update", {"domain": "example.com"})
        )
        setup.pending.answer(first["confirmation_id"], True, SecretValue("Echo-123"))
        result = await session.call_tool(
            "domain_transfer_in_code_update",
            {"domain": "example.com", "confirmation_id": first["confirmation_id"]},
        )

    assert "Echo-123" not in json.dumps(result.model_dump(mode="json"))


@pytest.mark.parametrize(
    "name", ["domain_transfer_unlock", "domain_authorization_code_reset", "domain_tags_replace"]
)
async def test_risky_changes_wait_for_the_confirmation(setup: Setup, name: str) -> None:
    arguments, *_ = CALLS[name]

    async with Client(setup.server) as session:
        result = data(await session.call_tool(name, arguments))

    assert result["status"] == "confirmation_pending"
    assert setup.gandi.calls == []
