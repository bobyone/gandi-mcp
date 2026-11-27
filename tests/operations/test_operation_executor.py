# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the operation rules (flow D), with doubles."""

from dataclasses import dataclass

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import (
    AccountNotFoundError,
    NoAccountError,
    ReadOnlyAccountError,
)
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.exceptions import ConfirmationMismatchError, ConfirmationRefusedError
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.gandi.exceptions import GandiNotFoundError
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.i18n.message import Message
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.fake_gandi_client import FakeGandiClient
from tests.doubles.hooked_secret_store import HookedSecretStore
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.scripted_interaction import ScriptedInteraction
from tests.doubles.scripted_operation import ScriptedOperation
from tests.doubles.source_translator import SourceTranslator
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")


@dataclass
class Setup:
    executor: OperationExecutor
    accounts: AccountService
    client: FakeGandiClient
    pending: PendingConfirmations


@pytest.fixture
async def setup() -> Setup:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    await accounts.add(
        AccountDraft(AccountName("Watch"), Environment.SANDBOX, read_only=True), TOKEN
    )
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
    client = FakeGandiClient()
    return Setup(
        OperationExecutor(accounts, secrets, client, confirmation), accounts, client, pending
    )


async def test_read_operation_on_the_default_account(setup: Setup) -> None:
    setup.client.outcomes.append(GandiResponse(200, [{"fqdn": "example.com"}], total_count=7))
    operation = ScriptedOperation(OperationCategory.READ, method="GET")

    result = await setup.executor.run(operation, None, ConfirmationContext())

    assert result == UntrustedResult([{"fqdn": "example.com"}], 7)
    call = setup.client.calls[0]
    assert (call.environment, call.token, call.path) == (
        Environment.SANDBOX,
        TOKEN,
        ("test", "example.com"),
    )


async def test_read_operation_allowed_on_a_read_only_account(setup: Setup) -> None:
    operation = ScriptedOperation(OperationCategory.READ, method="GET")

    result = await setup.executor.run(operation, AccountName("Watch"), ConfirmationContext())

    assert isinstance(result, UntrustedResult)


@pytest.mark.parametrize(
    "category",
    [OperationCategory.WRITE, OperationCategory.DESTRUCTIVE, OperationCategory.BILLABLE],
)
async def test_write_operations_refused_on_a_read_only_account(
    setup: Setup, category: OperationCategory
) -> None:
    interaction = ScriptedInteraction()

    with pytest.raises(ReadOnlyAccountError):
        await setup.executor.run(
            ScriptedOperation(category), AccountName("Watch"), ConfirmationContext(interaction)
        )

    assert setup.client.calls == []
    assert interaction.questions == []


async def test_plain_write_needs_no_confirmation(setup: Setup) -> None:
    interaction = ScriptedInteraction()

    await setup.executor.run(
        ScriptedOperation(OperationCategory.WRITE), None, ConfirmationContext(interaction)
    )

    assert interaction.questions == []
    assert len(setup.client.calls) == 1


async def test_destructive_operation_confirmed(setup: Setup) -> None:
    interaction = ScriptedInteraction()

    await setup.executor.run(
        ScriptedOperation(OperationCategory.DESTRUCTIVE), None, ConfirmationContext(interaction)
    )

    assert interaction.questions == ["Confirm on the sandbox account Perso: delete example.com"]
    assert len(setup.client.calls) == 1


async def test_refused_confirmation_has_no_effect(setup: Setup) -> None:
    with pytest.raises(ConfirmationRefusedError):
        await setup.executor.run(
            ScriptedOperation(OperationCategory.BILLABLE),
            None,
            ConfirmationContext(ScriptedInteraction(answer=False)),
        )

    assert setup.client.calls == []


async def test_pending_confirmation_then_resume(setup: Setup) -> None:
    operation = ScriptedOperation(OperationCategory.DESTRUCTIVE)

    first = await setup.executor.run(operation, None, ConfirmationContext())
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    assert setup.client.calls == []
    setup.pending.answer(first.confirmation_id, True)
    second = await setup.executor.run(operation, None, ConfirmationContext(), first.confirmation_id)

    assert isinstance(second, UntrustedResult)
    assert len(setup.client.calls) == 1


async def test_errors_pass_through(setup: Setup) -> None:
    setup.client.outcomes.append(GandiNotFoundError("missing"))

    with pytest.raises(GandiNotFoundError):
        await setup.executor.run(
            ScriptedOperation(OperationCategory.READ), None, ConfirmationContext()
        )


async def test_no_account() -> None:
    executor = OperationExecutor(
        AccountService(InMemoryPreferencesStore(), InMemorySecretStore(), StubTokenVerifier()),
        InMemorySecretStore(),
        FakeGandiClient(),
        ConfirmationService([], PendingConfirmations(300)),
    )

    with pytest.raises(NoAccountError):
        await executor.run(ScriptedOperation(OperationCategory.READ), None, ConfirmationContext())


async def test_a_confirmation_is_bound_to_the_account_environment(setup: Setup) -> None:
    operation = ScriptedOperation(OperationCategory.DESTRUCTIVE)
    first = await setup.executor.run(operation, None, ConfirmationContext())
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    setup.pending.answer(first.confirmation_id, True)
    production = PersonalAccessToken("pat_production_01234567")
    verifier = setup.accounts._verifier  # test inspection of the double
    assert isinstance(verifier, StubTokenVerifier)
    verifier.accept(Environment.PRODUCTION, production)
    await setup.accounts.change_environment(
        AccountName("Perso"), Environment.PRODUCTION, production
    )

    with pytest.raises(ConfirmationMismatchError):
        await setup.executor.run(operation, None, ConfirmationContext(), first.confirmation_id)
    assert setup.client.calls == []


async def test_an_operation_needing_a_secret_is_confirmed_on_the_page(setup: Setup) -> None:
    interaction = ScriptedInteraction()
    operation = ScriptedOperation(
        OperationCategory.WRITE, method="PUT", secret_label=Message("Authorization code")
    )

    first = await setup.executor.run(operation, None, ConfirmationContext(interaction))
    assert isinstance(first, ConfirmationDecision)
    assert first.confirmation_id is not None
    setup.pending.answer(first.confirmation_id, True, SecretValue("Auth-123"))
    second = await setup.executor.run(
        operation, None, ConfirmationContext(interaction), first.confirmation_id
    )

    assert isinstance(second, UntrustedResult)
    assert operation.secrets == [SecretValue("Auth-123")]
    assert "Confirm on" not in " ".join(interaction.questions)  # no form elicitation
    assert "Auth-123" not in operation.subject()


async def test_a_secret_operation_is_refused_on_a_read_only_account(setup: Setup) -> None:
    operation = ScriptedOperation(
        OperationCategory.WRITE, method="PUT", secret_label=Message("Authorization code")
    )

    with pytest.raises(ReadOnlyAccountError):
        await setup.executor.run(operation, AccountName("Watch"), ConfirmationContext())

    assert setup.pending._items == {}


async def test_a_read_only_toggle_during_the_token_read_stops_the_write() -> None:
    secrets, verifier = HookedSecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), TOKEN)
    pending = PendingConfirmations(300)
    client = FakeGandiClient()
    executor = OperationExecutor(accounts, secrets, client, ConfirmationService([], pending))

    async def lock() -> None:
        await accounts.update(AccountName("Perso"), read_only=True)

    secrets.reads, secrets.on_read, secrets.on_get = 0, 1, lock

    with pytest.raises(ReadOnlyAccountError):
        await executor.run(ScriptedOperation(OperationCategory.WRITE), None, ConfirmationContext())

    assert client.calls == []


async def test_a_public_read_needs_no_account() -> None:
    secrets, client = InMemorySecretStore(), FakeGandiClient()
    accounts = AccountService(InMemoryPreferencesStore(), secrets, StubTokenVerifier())
    executor = OperationExecutor(
        accounts, secrets, client, ConfirmationService([], PendingConfirmations(300))
    )
    operation = ScriptedOperation(OperationCategory.READ, method="GET", public=True)

    result = await executor.run(operation, None, ConfirmationContext())

    assert isinstance(result, UntrustedResult)
    assert (client.calls[0].environment, client.calls[0].token) == (Environment.PRODUCTION, None)


async def test_a_public_read_uses_the_environment_of_the_account_without_its_token(
    setup: Setup,
) -> None:
    operation = ScriptedOperation(OperationCategory.READ, method="GET", public=True)

    await setup.executor.run(operation, AccountName("Watch"), ConfirmationContext())

    assert (setup.client.calls[0].environment, setup.client.calls[0].token) == (
        Environment.SANDBOX,
        None,
    )


async def test_a_public_read_with_an_unknown_account_is_refused(setup: Setup) -> None:
    operation = ScriptedOperation(OperationCategory.READ, method="GET", public=True)

    with pytest.raises(AccountNotFoundError):
        await setup.executor.run(operation, AccountName("Nobody"), ConfirmationContext())

    assert not setup.client.calls


@pytest.mark.parametrize("category", [OperationCategory.WRITE, OperationCategory.DESTRUCTIVE])
async def test_a_public_operation_never_writes(setup: Setup, category: OperationCategory) -> None:
    operation = ScriptedOperation(category, public=True)

    with pytest.raises(TypeError):
        await setup.executor.run(operation, None, ConfirmationContext())

    assert not setup.client.calls
