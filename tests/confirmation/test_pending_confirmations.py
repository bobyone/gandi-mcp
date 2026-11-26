# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the registry of confirmations answered on local pages."""

import pytest

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation import pending_confirmations as module
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import (
    ConfirmationExpiredError,
    ConfirmationMismatchError,
    ConfirmationRefusedError,
)
from gandi_mcp.confirmation.pending_confirmation import PendingState
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.operation_category import OperationCategory


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def request(subject: str = "remove:perso") -> ConfirmationRequest:
    return ConfirmationRequest(
        subject,
        OperationCategory.DESTRUCTIVE,
        LocalizedText(Message("remove")),
        AccountName("Perso"),
        Environment.SANDBOX,
    )


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def registry(clock: Clock) -> PendingConfirmations:
    return PendingConfirmations(300, clock)


def test_accepted_confirmation_is_used_once(registry: PendingConfirmations) -> None:
    pending = registry.create(request())

    assert not registry.consume(pending.confirmation_id, "remove:perso")
    assert registry.answer(pending.confirmation_id, True).state is PendingState.ACCEPTED
    assert registry.consume(pending.confirmation_id, "remove:perso")
    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, "remove:perso")


def test_identifiers_are_random(registry: PendingConfirmations) -> None:
    first, second = registry.create(request()), registry.create(request())

    assert first.confirmation_id != second.confirmation_id
    assert len(first.confirmation_id) >= 20


def test_refused_confirmation(registry: PendingConfirmations) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, False)

    with pytest.raises(ConfirmationRefusedError):
        registry.consume(pending.confirmation_id, "remove:perso")
    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, "remove:perso")


def test_confirmation_for_another_operation(registry: PendingConfirmations) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, True)

    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, "remove:pro")
    assert registry.consume(pending.confirmation_id, "remove:perso")


def test_answering_twice_is_refused(registry: PendingConfirmations) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, True)

    with pytest.raises(ConfirmationMismatchError):
        registry.answer(pending.confirmation_id, False)
    with pytest.raises(ConfirmationMismatchError):
        registry.get(pending.confirmation_id)


def test_expiry(registry: PendingConfirmations, clock: Clock) -> None:
    pending = registry.create(request())
    clock.now += 301

    with pytest.raises(ConfirmationExpiredError):
        registry.answer(pending.confirmation_id, True)
    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, "remove:perso")


def test_answer_given_in_time_survives_the_deadline(
    registry: PendingConfirmations, clock: Clock
) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, True)
    clock.now += 100

    assert registry.consume(pending.confirmation_id, "remove:perso")


def test_unknown_and_cancelled(registry: PendingConfirmations) -> None:
    pending = registry.create(request())
    registry.cancel(pending.confirmation_id)
    registry.cancel("unknown")

    with pytest.raises(ConfirmationMismatchError):
        registry.get(pending.confirmation_id)


def test_expired_entries_are_purged_and_size_is_bounded(
    registry: PendingConfirmations, clock: Clock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_PENDING", 2)
    old = registry.create(request())
    clock.now += 301
    first = registry.create(request())
    clock.now += 1
    second = registry.create(request())
    third = registry.create(request())

    with pytest.raises(ConfirmationMismatchError):
        registry.get(old.confirmation_id)
    with pytest.raises(ConfirmationMismatchError):
        registry.get(first.confirmation_id)
    assert registry.get(second.confirmation_id) == second
    assert registry.get(third.confirmation_id) == third
