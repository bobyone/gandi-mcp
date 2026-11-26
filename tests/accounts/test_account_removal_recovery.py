# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The state of an account after each failure of its removal, and its recovery."""

import asyncio
from dataclasses import dataclass

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import AccountRemovalPendingError
from gandi_mcp.preferences.exceptions import PreferencesUnavailableError
from gandi_mcp.secrets.exceptions import SecretStoreUnavailableError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
PERSO = AccountName("Perso")


@dataclass
class World:
    preferences: InMemoryPreferencesStore
    secrets: InMemorySecretStore
    service: AccountService
    key: str


@pytest.fixture
async def world() -> World:
    preferences, secrets, verifier = (
        InMemoryPreferencesStore(),
        InMemorySecretStore(),
        StubTokenVerifier(),
    )
    verifier.accept(Environment.SANDBOX, TOKEN)
    service = AccountService(preferences, secrets, verifier)
    await service.add(AccountDraft(PERSO, Environment.SANDBOX), TOKEN)
    return World(preferences, secrets, service, (await service.resolve()).secret_key)


async def assert_usable(world: World) -> None:
    account = await world.service.resolve(PERSO)
    assert not account.removal_pending
    assert world.secrets.tokens == {world.key: TOKEN}


async def assert_pending_then_retry(world: World) -> None:
    listed = await world.service.list()
    assert [(str(a.name), a.removal_pending) for a in listed] == [("Perso", True)]
    with pytest.raises(AccountRemovalPendingError):
        await world.service.resolve(PERSO)
    world.preferences.fail_on_save = False
    world.secrets.unavailable = False
    world.secrets.delete_failure = None
    await world.service.remove(PERSO)
    assert await world.service.list() == ()
    assert world.secrets.tokens == {}


async def test_failure_to_mark_changes_nothing(world: World) -> None:
    world.preferences.fail_on_save_number = 1

    with pytest.raises(PreferencesUnavailableError):
        await world.service.remove(PERSO)

    await assert_usable(world)


async def test_keyring_failure_withdraws_the_mark(world: World) -> None:
    world.secrets.delete_failure = SecretStoreUnavailableError("locked")

    with pytest.raises(SecretStoreUnavailableError):
        await world.service.remove(PERSO)

    await assert_usable(world)


async def test_keyring_failure_and_unwritable_preferences_leave_a_pending_removal(
    world: World,
) -> None:
    world.secrets.delete_failure = SecretStoreUnavailableError("locked")
    world.preferences.fail_on_save_number = 2

    with pytest.raises(SecretStoreUnavailableError):
        await world.service.remove(PERSO)

    assert world.secrets.tokens == {world.key: TOKEN}
    await assert_pending_then_retry(world)


async def test_failure_after_removing_the_token_leaves_a_pending_removal(world: World) -> None:
    world.preferences.fail_on_save_number = 2

    with pytest.raises(PreferencesUnavailableError):
        await world.service.remove(PERSO)

    assert world.secrets.tokens == {}
    await assert_pending_then_retry(world)


async def test_cancellation_after_marking_leaves_a_pending_removal(world: World) -> None:
    world.secrets.delete_failure = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await world.service.remove(PERSO)

    await assert_pending_then_retry(world)


async def test_a_pending_account_refuses_every_other_change(world: World) -> None:
    world.preferences.fail_on_save_number = 2
    with pytest.raises(PreferencesUnavailableError):
        await world.service.remove(PERSO)

    with pytest.raises(AccountRemovalPendingError):
        await world.service.set_read_only(PERSO, True)
    with pytest.raises(AccountRemovalPendingError):
        await world.service.replace_token(PERSO, TOKEN)
