# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the registry of confirmations answered on local pages."""

import asyncio
import weakref
from collections.abc import Callable
from dataclasses import dataclass, field, replace

import pytest

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation import pending_confirmations as module
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.exceptions import (
    ConfirmationExpiredError,
    ConfirmationMismatchError,
    ConfirmationRefusedError,
    SecretInputMissingError,
)
from gandi_mcp.confirmation.pending_confirmation import PendingState
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations, loop_scheduler
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.secret_value import SecretValue


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


def test_accepted_confirmation_is_usable_until_the_deadline(
    registry: PendingConfirmations, clock: Clock
) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, True)
    clock.now += 299

    assert registry.consume(pending.confirmation_id, "remove:perso")


@pytest.mark.parametrize("accepted", [True, False])
def test_answered_confirmation_expires_at_the_deadline(
    registry: PendingConfirmations, clock: Clock, accepted: bool
) -> None:
    pending = registry.create(request())
    registry.answer(pending.confirmation_id, accepted)
    clock.now += 301

    with pytest.raises(ConfirmationExpiredError):
        registry.consume(pending.confirmation_id, "remove:perso")
    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, "remove:perso")


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


@dataclass
class ManualScheduler:
    """Records the scheduled callbacks; the test decides when they run."""

    calls: list[tuple[float, Callable[[], None]]] = field(default_factory=list)

    def __call__(self, delay: float, callback: Callable[[], None]) -> None:
        self.calls.append((delay, callback))


def secret_request() -> ConfirmationRequest:
    return replace(request(), secret_input=SecretInput(Message("Authorization code")))


def test_an_acceptance_needs_the_secret_asked_for() -> None:
    registry = PendingConfirmations(300)
    pending = registry.create(secret_request())

    with pytest.raises(SecretInputMissingError):
        registry.answer(pending.confirmation_id, True)
    answered = registry.answer(pending.confirmation_id, True, SecretValue("Auth-123"))

    assert answered.secret == SecretValue("Auth-123")
    assert "Auth-123" not in repr(answered)
    used = registry.consume(pending.confirmation_id, pending.request.subject)
    assert used is not None
    assert used.secret == SecretValue("Auth-123")


def test_a_secret_is_dropped_when_refused_or_not_asked_for() -> None:
    registry = PendingConfirmations(300)
    refused = registry.create(secret_request())
    plain = registry.create(request())

    assert registry.answer(refused.confirmation_id, False, SecretValue("x")).secret is None
    assert registry.answer(plain.confirmation_id, True, SecretValue("x")).secret is None


def test_a_typed_secret_is_released_at_the_deadline_without_a_new_call() -> None:
    clock, scheduler = Clock(), ManualScheduler()
    registry = PendingConfirmations(300, clock, scheduler)
    pending = registry.create(secret_request())
    plain = registry.create(request("other"))
    clock.now += 100

    registry.answer(pending.confirmation_id, True, SecretValue("Auth-123"))
    registry.answer(plain.confirmation_id, True)

    assert len(scheduler.calls) == 1
    delay, release = scheduler.calls[0]
    assert delay == 200
    release()
    with pytest.raises(ConfirmationMismatchError):
        registry.consume(pending.confirmation_id, pending.request.subject)
    assert registry.consume(plain.confirmation_id, "other") is not None


def test_timer_does_not_keep_a_consumed_confirmation_alive() -> None:
    scheduler = ManualScheduler()
    registry = PendingConfirmations(300, Clock(), scheduler)
    pending = registry.create(secret_request())
    answered = weakref.ref(registry.answer(pending.confirmation_id, True, SecretValue("Auth-123")))
    registry.consume(pending.confirmation_id, pending.request.subject)

    assert answered() is None
    scheduler.calls[0][1]()

    assert registry._items == {}


@pytest.mark.anyio
async def test_the_default_scheduler_uses_the_running_loop() -> None:
    called: list[bool] = []

    loop_scheduler(0, lambda: called.append(True))
    await asyncio.sleep(0.01)

    assert called == [True]


def test_the_default_scheduler_needs_a_loop() -> None:
    loop_scheduler(0, lambda: None)  # no running loop: nothing is scheduled
