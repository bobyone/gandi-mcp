# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the registry of token entry sessions."""

import pytest

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.token_entry import token_entry_sessions as module
from gandi_mcp.token_entry.exceptions import SessionExpiredError, SessionUsedError
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose

TARGET = TokenEntryTarget(TokenPurpose.ADD, AccountName("Perso"), Environment.SANDBOX)


class Clock:
    def __init__(self) -> None:
        self.now = 50.0

    def __call__(self) -> float:
        return self.now


def test_session_is_used_once() -> None:
    sessions = TokenEntrySessions(600)
    session = sessions.open(TARGET)

    assert sessions.peek(session.session_id) == session
    assert sessions.use(session.session_id) == session
    with pytest.raises(SessionUsedError):
        sessions.use(session.session_id)


def test_session_expires() -> None:
    clock = Clock()
    sessions = TokenEntrySessions(600, clock)
    session = sessions.open(TARGET)
    clock.now += 601

    with pytest.raises(SessionExpiredError):
        sessions.peek(session.session_id)
    with pytest.raises(SessionUsedError):
        sessions.use(session.session_id)


def test_closed_and_unknown_sessions() -> None:
    sessions = TokenEntrySessions(600)
    session = sessions.open(TARGET)
    sessions.close(session.session_id)
    sessions.close("unknown")

    with pytest.raises(SessionUsedError):
        sessions.peek(session.session_id)


def test_sessions_are_bounded_and_purged(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "MAX_SESSIONS", 2)
    clock = Clock()
    sessions = TokenEntrySessions(600, clock)
    expired = sessions.open(TARGET)
    clock.now += 601
    first, second = sessions.open(TARGET), sessions.open(TARGET)
    clock.now += 1
    third = sessions.open(TARGET)

    for gone in (expired, first):
        with pytest.raises(SessionUsedError):
            sessions.peek(gone.session_id)
    assert sessions.peek(second.session_id) == second
    assert sessions.peek(third.session_id) == third
