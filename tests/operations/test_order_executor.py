# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the order rules (algorithm G), with doubles."""

from dataclasses import dataclass, field
from decimal import Decimal

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import ReadOnlyAccountError
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.exceptions import ConfirmationMismatchError
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.domains.contacts.domain_contact import ContactType, DomainContact
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.money import Money
from gandi_mcp.domains.quotes.exceptions import NotAvailableError
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_provider import QuoteProvider
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.operations.domain.billable.register_domain import RegisterDomain
from gandi_mcp.operations.domain.billable.renew_domain import RenewDomain
from gandi_mcp.operations.domain.billable.transfer_in_domain import TransferInDomain
from gandi_mcp.operations.exceptions import DryRunRejectedError, PriceChangedError
from gandi_mcp.operations.order_executor import OrderExecutor
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.fake_gandi_client import FakeGandiClient
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.scripted_interaction import ScriptedInteraction
from tests.doubles.source_translator import SourceTranslator
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
ORG = OrganizationId("5a53edc7-b514-416a-98c2-2d477a288eb9")
OWNER = DomainContact(
    ContactType.INDIVIDUAL, "Ada", "Lovelace", "ada@example.org", "1 rue", "Paris", "75001", "FR"
)


@dataclass
class StubQuotes(QuoteProvider):
    prices: list[str] = field(default_factory=lambda: ["24.96"])
    failure: Exception | None = None
    requests: list[QuoteRequest] = field(default_factory=list)

    async def quote(
        self, environment: Environment, token: PersonalAccessToken, request: QuoteRequest
    ) -> Quote:
        self.requests.append(request)
        if self.failure is not None:
            raise self.failure
        price = self.prices.pop(0) if len(self.prices) > 1 else self.prices[0]
        return Quote(request, Money(Decimal(price), "EUR"), Money(Decimal(price), "EUR"))


@dataclass
class Setup:
    orders: OrderExecutor
    accounts: AccountService
    client: FakeGandiClient
    quotes: StubQuotes
    pending: PendingConfirmations
    translator: SourceTranslator


@pytest.fixture
async def setup() -> Setup:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    await accounts.add(AccountDraft(AccountName("Watch"), Environment.SANDBOX, True), TOKEN)
    pending, translator = PendingConfirmations(300), SourceTranslator()
    confirmation = ConfirmationService(
        [
            ElicitationChannel(translator),
            LocalLinkChannel(
                pending, FakeConfirmationPage(), LinkPresenter(FakeBrowser()), translator
            ),
        ],
        pending,
    )
    client, quotes = FakeGandiClient(), StubQuotes()
    orders = OrderExecutor(
        accounts, secrets, client, confirmation, quotes=quotes, translator=translator
    )
    return Setup(orders, accounts, client, quotes, pending, translator)


def register() -> RegisterDomain:
    return RegisterDomain(DomainName("example.com"), RegistrationDuration(2), DomainContacts(OWNER))


async def test_quote_dry_run_confirm_recheck_order(setup: Setup) -> None:
    interaction = ScriptedInteraction()
    setup.client.outcomes.extend(
        [GandiResponse(200, {"status": "success"}), GandiResponse(202, {"message": "ok"})]
    )

    result = await setup.orders.run(register(), None, ConfirmationContext(interaction))

    assert isinstance(result, UntrustedResult)
    assert [call.dry_run for call in setup.client.calls] == [True, False]
    assert len(setup.quotes.requests) == 2
    assert interaction.questions == [
        "Confirm on the sandbox account Perso: register example.com for 2 years: 24.96 EUR "
        "including taxes"
    ]


async def test_paying_organization_comes_from_the_call_then_the_account(setup: Setup) -> None:
    other = OrganizationId("0b1c2d3e-4f50-4617-8899-aabbccddeeff")
    await setup.accounts.update(AccountName("Perso"), paying_organization=ORG)
    interaction = ScriptedInteraction()

    await setup.orders.run(register(), None, ConfirmationContext(interaction))
    await setup.orders.run(register(), None, ConfirmationContext(interaction), None, other)

    assert [request.paying_organization for request in setup.quotes.requests] == [
        ORG,
        ORG,
        other,
        other,
    ]
    assert setup.client.calls[0].query == {"sharing_id": str(ORG)}
    assert "paid by the organization" in interaction.questions[0]


async def test_read_only_accounts_never_buy(setup: Setup) -> None:
    with pytest.raises(ReadOnlyAccountError):
        await setup.orders.run(register(), AccountName("Watch"), ConfirmationContext())

    assert setup.quotes.requests == []


async def test_an_unavailable_domain_stops_before_anything(setup: Setup) -> None:
    setup.quotes.failure = NotAvailableError("taken", "unavailable")

    with pytest.raises(NotAvailableError):
        await setup.orders.run(register(), None, ConfirmationContext(ScriptedInteraction()))

    assert setup.client.calls == []


async def test_a_rejected_dry_run_explains_why(setup: Setup) -> None:
    setup.client.outcomes.append(
        GandiResponse(
            200,
            {
                "status": "error",
                "errors": [
                    {"name": "owner.given", "description": "must  match"},
                    "junk",
                    {"name": " "},
                ],
            },
        )
    )

    with pytest.raises(DryRunRejectedError) as raised:
        await setup.orders.run(register(), None, ConfirmationContext(ScriptedInteraction()))

    assert raised.value.details == ("owner.given: must match",)
    assert len(setup.client.calls) == 1


async def test_a_price_change_cancels_the_order(setup: Setup) -> None:
    setup.quotes.prices = ["24.96", "29.99"]
    setup.client.outcomes.append(GandiResponse(200, {"status": "success"}))

    with pytest.raises(PriceChangedError):
        await setup.orders.run(register(), None, ConfirmationContext(ScriptedInteraction()))

    assert [call.dry_run for call in setup.client.calls] == [True]


async def test_resumed_on_the_page_at_the_same_price(setup: Setup) -> None:
    renew = RenewDomain(DomainName("example.com"), RegistrationDuration(1))
    setup.client.outcomes.append(GandiResponse(200, {"status": "success"}))

    first = await setup.orders.run(renew, None, ConfirmationContext())
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    setup.pending.answer(first.confirmation_id, True)
    second = await setup.orders.run(renew, None, ConfirmationContext(), first.confirmation_id)

    assert isinstance(second, UntrustedResult)
    assert [call.dry_run for call in setup.client.calls] == [True, False]


async def test_a_new_price_does_not_match_the_confirmation(setup: Setup) -> None:
    renew = RenewDomain(DomainName("example.com"), RegistrationDuration(1))
    first = await setup.orders.run(renew, None, ConfirmationContext())
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    setup.pending.answer(first.confirmation_id, True)
    setup.quotes.prices = ["30.00"]

    with pytest.raises(ConfirmationMismatchError):
        await setup.orders.run(renew, None, ConfirmationContext(), first.confirmation_id)


async def test_a_transfer_asks_for_the_code_on_the_page(setup: Setup) -> None:
    interaction = ScriptedInteraction()
    transfer = TransferInDomain(
        DomainName("example.com"), RegistrationDuration(1), DomainContacts(OWNER)
    )

    first = await setup.orders.run(transfer, None, ConfirmationContext(interaction))
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    setup.pending.answer(first.confirmation_id, True, SecretValue("Auth-123"))
    await setup.orders.run(transfer, None, ConfirmationContext(interaction), first.confirmation_id)

    assert interaction.questions == ["Open this page to confirm or refuse the operation."]
    body = setup.client.calls[-1].body
    assert isinstance(body, dict)
    assert body["authinfo"] == "Auth-123"
    assert not any(call.dry_run for call in setup.client.calls)
