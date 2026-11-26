# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the system browser, with ``webbrowser`` replaced."""

import webbrowser

import pytest

from gandi_mcp.interaction.system.system_browser import SystemBrowser

pytestmark = pytest.mark.anyio


async def test_opens_local_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    opened: list[str] = []

    def fake_open(url: str, _new: int) -> bool:
        opened.append(url)
        return True

    monkeypatch.setattr(webbrowser, "open", fake_open)

    assert await SystemBrowser().open("http://127.0.0.1:8123/x")
    assert opened == ["http://127.0.0.1:8123/x"]


@pytest.mark.parametrize("outcome", [False, webbrowser.Error("none")])
async def test_reports_a_missing_browser(
    monkeypatch: pytest.MonkeyPatch, outcome: bool | Exception
) -> None:
    def fake_open(_url: str, _new: int) -> bool:
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(webbrowser, "open", fake_open)

    assert not await SystemBrowser().open("http://localhost:8123/x")


@pytest.mark.parametrize(
    "url", ["https://127.0.0.1/x", "http://example.com/x", "file:///etc/passwd", "javascript:x"]
)
async def test_refuses_other_addresses(url: str) -> None:
    with pytest.raises(ValueError, match="local"):
        await SystemBrowser().open(url)
