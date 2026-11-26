# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the start of token entry sessions, with doubles."""

import pytest

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.token_entry.exceptions import SessionUsedError, TokenEntryUnavailableError
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.fake_token_entry_page import FakeTokenEntryPage
from tests.doubles.scripted_interaction import ScriptedInteraction
from tests.doubles.source_translator import SourceTranslator

pytestmark = pytest.mark.anyio

TARGET = TokenEntryTarget(TokenPurpose.ADD, AccountName("Perso"), Environment.SANDBOX)


def service(browser: FakeBrowser, sessions: TokenEntrySessions) -> TokenEntryService:
    return TokenEntryService(
        sessions, FakeTokenEntryPage(), LinkPresenter(browser), SourceTranslator()
    )


async def test_offers_the_page_through_url_elicitation() -> None:
    browser, sessions, interaction = FakeBrowser(), TokenEntrySessions(600), ScriptedInteraction()

    session = await service(browser, sessions).start(TARGET, interaction, "fr")

    assert interaction.opened == [f"http://127.0.0.1:1/token/{session.session_id}"]
    assert interaction.questions == [
        "Open this page to enter the Personal Access Token of the account Perso."
    ]
    assert sessions.peek(session.session_id) == session


async def test_opens_the_browser_without_elicitation() -> None:
    browser, sessions = FakeBrowser(), TokenEntrySessions(600)

    session = await service(browser, sessions).start(TARGET, None, None)

    assert browser.opened == [f"http://127.0.0.1:1/token/{session.session_id}"]


async def test_closes_the_session_when_the_page_cannot_be_shown() -> None:
    browser, sessions = FakeBrowser(available=False), TokenEntrySessions(600)
    page = FakeTokenEntryPage()
    entry = TokenEntryService(sessions, page, LinkPresenter(browser), SourceTranslator())

    with pytest.raises(TokenEntryUnavailableError):
        await entry.start(TARGET, ScriptedInteraction(links=False), None)

    with pytest.raises(SessionUsedError):
        sessions.peek(page.opened[0].session_id)
