# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the chain of confirmation channels, with doubles."""

from dataclasses import dataclass, replace

import pytest

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_option import ConfirmationOption
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.exceptions import (
    ConfirmationMismatchError,
    ConfirmationRefusedError,
    ConfirmationUnavailableError,
)
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.secret_value import SecretValue
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_confirmation_page import FakeConfirmationPage
from tests.doubles.scripted_interaction import ScriptedInteraction
from tests.doubles.source_translator import SourceTranslator

pytestmark = pytest.mark.anyio


def request(
    environment: Environment = Environment.PRODUCTION, secret_input: SecretInput | None = None
) -> ConfirmationRequest:
    return ConfirmationRequest(
        "domain.delete:example.com",
        OperationCategory.DESTRUCTIVE,
        LocalizedText(Message("delete {domain}"), {"domain": "example.com"}),
        AccountName("Pro"),
        environment,
        secret_input,
    )


@dataclass
class Chain:
    service: ConfirmationService
    pending: PendingConfirmations
    page: FakeConfirmationPage
    browser: FakeBrowser
    translator: SourceTranslator


@pytest.fixture
def chain() -> Chain:
    pending, page, browser, translator = (
        PendingConfirmations(300),
        FakeConfirmationPage(),
        FakeBrowser(),
        SourceTranslator(),
    )
    channels = [
        ElicitationChannel(translator),
        LocalLinkChannel(pending, page, LinkPresenter(browser), translator),
    ]
    return Chain(ConfirmationService(channels, pending), pending, page, browser, translator)


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        (Environment.PRODUCTION, "Confirm on the production account Pro: delete example.com"),
        (Environment.SANDBOX, "Confirm on the sandbox account Pro: delete example.com"),
    ],
)
async def test_elicitation_names_account_and_environment(
    chain: Chain, environment: Environment, expected: str
) -> None:
    interaction = ScriptedInteraction()

    decision = await chain.service.confirm(
        request(environment), ConfirmationContext(interaction, locale="fr")
    )

    assert decision.accepted
    assert interaction.questions == [expected]
    assert set(chain.translator.locales) == {"fr"}


async def test_elicitation_refused(chain: Chain) -> None:
    with pytest.raises(ConfirmationRefusedError):
        await chain.service.confirm(
            request(), ConfirmationContext(ScriptedInteraction(answer=False))
        )


async def test_local_page_through_url_elicitation(chain: Chain) -> None:
    interaction = ScriptedInteraction(confirmations=False)

    decision = await chain.service.confirm(request(), ConfirmationContext(interaction))

    assert not decision.accepted
    assert decision.confirmation_id is not None
    assert interaction.opened == [f"http://127.0.0.1:1/confirm/{decision.confirmation_id}"]
    assert chain.browser.opened == []


async def test_local_page_in_the_browser_without_elicitation(chain: Chain) -> None:
    decision = await chain.service.confirm(request(), ConfirmationContext())

    assert decision.confirmation_id is not None
    assert chain.browser.opened == [f"http://127.0.0.1:1/confirm/{decision.confirmation_id}"]


async def test_local_page_that_cannot_be_shown(chain: Chain) -> None:
    chain.browser.available = False

    with pytest.raises(ConfirmationUnavailableError):
        await chain.service.confirm(request(), ConfirmationContext())

    pending = chain.page.opened[0]
    with pytest.raises(ConfirmationMismatchError):
        chain.pending.get(pending.confirmation_id)


async def test_url_elicitation_declined(chain: Chain) -> None:
    interaction = ScriptedInteraction(confirmations=False, answer=False)

    with pytest.raises(ConfirmationUnavailableError):
        await chain.service.confirm(request(), ConfirmationContext(interaction))


async def test_resuming_a_confirmation_answered_on_the_page(chain: Chain) -> None:
    decision = await chain.service.confirm(request(), ConfirmationContext())
    assert decision.confirmation_id is not None

    waiting = await chain.service.confirm(
        request(), ConfirmationContext(), decision.confirmation_id
    )
    chain.pending.answer(decision.confirmation_id, True)
    resumed = await chain.service.confirm(
        request(), ConfirmationContext(), decision.confirmation_id
    )

    assert not waiting.accepted
    assert waiting.confirmation_id == decision.confirmation_id
    assert resumed.accepted


async def test_a_model_given_identifier_is_not_a_confirmation(chain: Chain) -> None:
    with pytest.raises(ConfirmationMismatchError):
        await chain.service.confirm(request(), ConfirmationContext(), "invented")


async def test_no_channel(chain: Chain) -> None:
    service = ConfirmationService([ElicitationChannel(chain.translator)], chain.pending)

    with pytest.raises(ConfirmationUnavailableError):
        await service.confirm(request(), ConfirmationContext())


async def test_elicitation_channel_without_interaction() -> None:
    channel = ElicitationChannel(SourceTranslator())

    assert not channel.available(ConfirmationContext())
    with pytest.raises(ConfirmationRefusedError):
        await channel.confirm(request(), ConfirmationContext())


async def test_secret_requests_skip_channels_that_cannot_collect_secrets(chain: Chain) -> None:
    interaction = ScriptedInteraction()
    asks_secret = request(secret_input=SecretInput(Message("Authorization code")))

    decision = await chain.service.confirm(asks_secret, ConfirmationContext(interaction))

    assert interaction.questions == ["Open this page to confirm or refuse the operation."]
    assert decision.confirmation_id is not None
    assert interaction.opened == [f"http://127.0.0.1:1/confirm/{decision.confirmation_id}"]


async def test_the_secret_typed_on_the_page_comes_back_once(chain: Chain) -> None:
    asks_secret = request(secret_input=SecretInput(Message("Authorization code")))
    decision = await chain.service.confirm(asks_secret, ConfirmationContext())
    assert decision.confirmation_id is not None

    chain.pending.answer(decision.confirmation_id, True, SecretValue("Auth-123"))
    resumed = await chain.service.confirm(
        asks_secret, ConfirmationContext(), decision.confirmation_id
    )

    assert resumed.accepted
    assert resumed.secret == SecretValue("Auth-123")
    assert "Auth-123" not in repr(resumed)
    with pytest.raises(ConfirmationMismatchError):
        await chain.service.confirm(asks_secret, ConfirmationContext(), decision.confirmation_id)


OPTION = ConfirmationOption(Message("Create a snapshot first"))


@pytest.mark.parametrize("chosen", [True, False])
async def test_elicitation_offers_the_option(chain: Chain, chosen: bool) -> None:
    interaction = ScriptedInteraction(option_answer=chosen)
    offered = replace(request(), option=OPTION)

    decision = await chain.service.confirm(offered, ConfirmationContext(interaction))

    assert decision.accepted
    assert decision.option_chosen is chosen
    assert interaction.options == [("Create a snapshot first", True)]


async def test_elicitation_with_an_option_can_be_refused(chain: Chain) -> None:
    offered = replace(request(), option=OPTION)

    with pytest.raises(ConfirmationRefusedError):
        await chain.service.confirm(offered, ConfirmationContext(ScriptedInteraction(answer=False)))


async def test_the_option_chosen_on_a_local_page_comes_back_on_resume(chain: Chain) -> None:
    offered = replace(request(), option=OPTION)
    pending = await chain.service.confirm(
        offered, ConfirmationContext(ScriptedInteraction(confirmations=False, links=False))
    )
    assert pending.confirmation_id is not None
    chain.pending.answer(pending.confirmation_id, True, option_chosen=True)

    decision = await chain.service.confirm(offered, ConfirmationContext(), pending.confirmation_id)

    assert decision.accepted
    assert decision.option_chosen
