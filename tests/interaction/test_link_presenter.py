# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the presentation of local pages."""

import pytest

from gandi_mcp.interaction.link_presenter import LinkPresenter
from tests.doubles.fake_browser import FakeBrowser
from tests.doubles.scripted_interaction import ScriptedInteraction

pytestmark = pytest.mark.anyio

URL = "http://127.0.0.1:1/page"


async def test_prefers_url_elicitation() -> None:
    browser, interaction = FakeBrowser(), ScriptedInteraction()

    assert await LinkPresenter(browser).present(URL, "Open", interaction)
    assert interaction.opened == [URL]
    assert browser.opened == []


@pytest.mark.parametrize("interaction", [None, ScriptedInteraction(links=False)])
async def test_falls_back_to_the_browser(interaction: ScriptedInteraction | None) -> None:
    browser = FakeBrowser(available=False)

    assert not await LinkPresenter(browser).present(URL, "Open", interaction)
    assert browser.opened == [URL]
