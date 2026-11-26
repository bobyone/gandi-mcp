# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the account rules, with doubles of the stores and the verifier."""

from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import (
    AccountNotFoundError,
    DuplicateAccountError,
    NoAccountError,
    TokenRejectedError,
    WritesNotConfirmedError,
)
from gandi_mcp.gandi.exceptions import GandiUnavailableError
from gandi_mcp.preferences.exceptions import PreferencesUnavailableError
from gandi_mcp.secrets.exceptions import SecretStoreUnavailableError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

SANDBOX_TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
PRODUCTION_TOKEN = PersonalAccessToken("pat_production_0123456789")
OTHER_TOKEN = PersonalAccessToken("pat_other_0123456789")


@dataclass
class World:
    preferences: InMemoryPreferencesStore
    secrets: InMemorySecretStore
    verifier: StubTokenVerifier
    service: AccountService


@pytest.fixture
def world() -> World:
    preferences, secrets, verifier = (
        InMemoryPreferencesStore(),
        InMemorySecretStore(),
        StubTokenVerifier(),
    )
    verifier.accept(Environment.SANDBOX, SANDBOX_TOKEN)
    verifier.accept(Environment.SANDBOX, OTHER_TOKEN)
    verifier.accept(Environment.PRODUCTION, PRODUCTION_TOKEN)
    return World(preferences, secrets, verifier, AccountService(preferences, secrets, verifier))


def draft(name: str, environment: Environment = Environment.SANDBOX) -> AccountDraft:
    return AccountDraft(AccountName(name), environment)


async def add(world: World, *names: str) -> None:
    for name in names:
        await world.service.add(draft(name), SANDBOX_TOKEN)


async def test_first_account_becomes_the_default(world: World) -> None:
    added = await world.service.add(draft("Perso"), SANDBOX_TOKEN)

    assert added.account.is_default
    assert added.identity == AccountIdentity("ada", "Ada Lovelace")
    account = await world.service.resolve()
    assert account.name == AccountName("Perso")
    assert world.secrets.tokens == {account.secret_key: SANDBOX_TOKEN}


async def test_later_accounts_keep_the_default(world: World) -> None:
    await add(world, "Perso")

    added = await world.service.add(
        AccountDraft(AccountName("Pro"), Environment.PRODUCTION, read_only=True), PRODUCTION_TOKEN
    )

    assert not added.account.is_default
    assert added.account.read_only
    assert [str(a.name) for a in await world.service.list()] == ["Perso", "Pro"]


async def test_list_is_sorted_and_secret_free(world: World) -> None:
    await add(world, "zeta", "Alpha", "beta")

    accounts = await world.service.list()

    assert [str(a.name) for a in accounts] == ["Alpha", "beta", "zeta"]
    assert [a.is_default for a in accounts] == [False, False, True]
    assert all(not hasattr(a, "secret_key") for a in accounts)


async def test_duplicate_names_ignore_case(world: World) -> None:
    await add(world, "Perso")

    with pytest.raises(DuplicateAccountError):
        await world.service.add(draft("PERSO"), SANDBOX_TOKEN)
    assert world.verifier.calls == [Environment.SANDBOX]


async def test_rejected_token_keeps_nothing(world: World) -> None:
    with pytest.raises(TokenRejectedError):
        await world.service.add(draft("Perso", Environment.PRODUCTION), SANDBOX_TOKEN)

    assert world.secrets.tokens == {}
    assert await world.service.list() == ()


async def test_gandi_unavailable_keeps_nothing(world: World) -> None:
    world.verifier.failure = GandiUnavailableError("down")

    with pytest.raises(GandiUnavailableError):
        await world.service.add(draft("Perso"), SANDBOX_TOKEN)

    assert world.secrets.tokens == {}


async def test_unavailable_secret_store_keeps_nothing(world: World) -> None:
    world.secrets.unavailable = True

    with pytest.raises(SecretStoreUnavailableError):
        await world.service.add(draft("Perso"), SANDBOX_TOKEN)

    assert world.preferences.saves == 0


async def test_failed_save_removes_the_stored_token(world: World) -> None:
    world.preferences.fail_on_save = True

    with pytest.raises(PreferencesUnavailableError):
        await world.service.add(draft("Perso"), SANDBOX_TOKEN)

    assert world.secrets.tokens == {}


async def test_resolve_errors(world: World) -> None:
    with pytest.raises(NoAccountError):
        await world.service.resolve()
    await add(world, "Perso")
    with pytest.raises(AccountNotFoundError):
        await world.service.resolve(AccountName("Pro"))
    assert (await world.service.resolve(AccountName("PERSO"))).name == AccountName("Perso")


async def test_rename_keeps_token_and_default(world: World) -> None:
    await add(world, "Perso", "Pro")
    before = await world.service.resolve(AccountName("Perso"))

    renamed = await world.service.rename(AccountName("Perso"), AccountName("Home"))

    assert renamed.name == AccountName("Home")
    assert renamed.is_default
    after = await world.service.resolve()
    assert after.name == AccountName("Home")
    assert after.secret_key == before.secret_key


async def test_rename_of_another_account_keeps_the_default(world: World) -> None:
    await add(world, "Perso", "Pro")

    renamed = await world.service.rename(AccountName("Pro"), AccountName("Work"))

    assert not renamed.is_default
    assert (await world.service.resolve()).name == AccountName("Perso")


async def test_rename_may_change_case_only(world: World) -> None:
    await add(world, "perso")

    renamed = await world.service.rename(AccountName("perso"), AccountName("Perso"))

    assert str(renamed.name) == "Perso"


async def test_rename_refuses_a_used_name(world: World) -> None:
    await add(world, "Perso", "Pro")

    with pytest.raises(DuplicateAccountError):
        await world.service.rename(AccountName("Perso"), AccountName("pro"))


async def test_set_default(world: World) -> None:
    await add(world, "Perso", "Pro")

    summary = await world.service.set_default(AccountName("pro"))

    assert summary.is_default
    assert (await world.service.resolve()).name == AccountName("Pro")


async def test_set_read_only(world: World) -> None:
    await add(world, "Perso")

    summary = await world.service.set_read_only(AccountName("Perso"), True)

    assert summary.read_only
    assert summary.is_default
    assert (await world.service.resolve()).read_only


async def test_replace_token(world: World) -> None:
    await add(world, "Perso")
    key = (await world.service.resolve()).secret_key

    verified = await world.service.replace_token(AccountName("Perso"), OTHER_TOKEN)

    assert verified.identity.username == "ada"
    assert world.secrets.tokens == {key: OTHER_TOKEN}


async def test_replace_token_rejected_keeps_the_old_one(world: World) -> None:
    await add(world, "Perso")
    key = (await world.service.resolve()).secret_key

    with pytest.raises(TokenRejectedError):
        await world.service.replace_token(AccountName("Perso"), PRODUCTION_TOKEN)

    assert world.secrets.tokens == {key: SANDBOX_TOKEN}


async def test_change_environment(world: World) -> None:
    await add(world, "Perso")
    key = (await world.service.resolve()).secret_key

    verified = await world.service.change_environment(
        AccountName("Perso"), Environment.PRODUCTION, PRODUCTION_TOKEN
    )

    assert verified.account.environment is Environment.PRODUCTION
    assert world.secrets.tokens == {key: PRODUCTION_TOKEN}
    assert world.verifier.calls[-1] is Environment.PRODUCTION


async def test_change_environment_needs_a_token_valid_there(world: World) -> None:
    await add(world, "Perso")

    with pytest.raises(TokenRejectedError):
        await world.service.change_environment(
            AccountName("Perso"), Environment.PRODUCTION, SANDBOX_TOKEN
        )

    assert (await world.service.resolve()).environment is Environment.SANDBOX


async def test_change_environment_restores_the_token_when_saving_fails(world: World) -> None:
    await add(world, "Perso")
    key = (await world.service.resolve()).secret_key
    world.preferences.fail_on_save = True

    with pytest.raises(PreferencesUnavailableError):
        await world.service.change_environment(
            AccountName("Perso"), Environment.PRODUCTION, PRODUCTION_TOKEN
        )

    assert world.secrets.tokens == {key: SANDBOX_TOKEN}


async def test_remove_default_promotes_the_first_remaining_account(world: World) -> None:
    await add(world, "Perso", "zeta", "Beta")
    key = (await world.service.resolve()).secret_key

    removal = await world.service.remove(AccountName("perso"))

    assert removal.removed == AccountName("Perso")
    assert removal.new_default == AccountName("Beta")
    assert key not in world.secrets.tokens
    assert (await world.service.resolve()).name == AccountName("Beta")


async def test_remove_another_account_keeps_the_default(world: World) -> None:
    await add(world, "Perso", "Pro")

    removal = await world.service.remove(AccountName("Pro"))

    assert removal.new_default is None
    assert (await world.service.resolve()).name == AccountName("Perso")


async def test_remove_the_last_account(world: World) -> None:
    await add(world, "Perso")

    removal = await world.service.remove(AccountName("Perso"))

    assert removal.new_default is None
    assert await world.service.list() == ()
    assert world.secrets.tokens == {}


async def test_remove_keeps_the_account_when_the_token_cannot_be_removed(
    world: World,
) -> None:
    await add(world, "Perso")
    world.secrets.unavailable = True

    with pytest.raises(SecretStoreUnavailableError):
        await world.service.remove(AccountName("Perso"))

    assert len(await world.service.list()) == 1
    world.secrets.unavailable = False
    await world.service.remove(AccountName("Perso"))
    assert await world.service.list() == ()
    assert world.secrets.tokens == {}


async def test_remove_tolerates_an_already_missing_token(world: World) -> None:
    await add(world, "Perso")
    world.secrets.tokens.clear()

    removal = await world.service.remove(AccountName("Perso"))

    assert removal.removed == AccountName("Perso")
    assert await world.service.list() == ()


async def test_remove_can_be_retried_when_saving_fails(world: World) -> None:
    await add(world, "Perso")
    world.preferences.fail_on_save = True

    with pytest.raises(PreferencesUnavailableError):
        await world.service.remove(AccountName("Perso"))

    assert len(await world.service.list()) == 1
    world.preferences.fail_on_save = False
    await world.service.remove(AccountName("Perso"))
    assert await world.service.list() == ()
    assert world.secrets.tokens == {}


@pytest.mark.parametrize("operation", ["rename", "set_default", "set_read_only", "remove"])
async def test_unknown_account(world: World, operation: str) -> None:
    await add(world, "Perso")
    missing = AccountName("Nope")
    calls: dict[str, Coroutine[Any, Any, object]] = {
        "rename": world.service.rename(missing, AccountName("X")),
        "set_default": world.service.set_default(missing),
        "set_read_only": world.service.set_read_only(missing, True),
        "remove": world.service.remove(missing),
    }
    call = calls.pop(operation)
    for unused in calls.values():
        unused.close()

    with pytest.raises(AccountNotFoundError):
        await call


async def test_combined_update_is_applied_in_one_save(world: World) -> None:
    await add(world, "Perso", "Pro")
    saves = world.preferences.saves

    summary = await world.service.update(
        AccountName("Pro"), new_name=AccountName("Work"), read_only=True, make_default=True
    )

    assert (summary.name, summary.read_only, summary.is_default) == (
        AccountName("Work"),
        True,
        True,
    )
    assert world.preferences.saves == saves + 1


async def test_combined_update_changes_nothing_when_a_part_is_refused(world: World) -> None:
    await add(world, "Perso", "Pro")
    before = world.preferences.preferences

    with pytest.raises(DuplicateAccountError):
        await world.service.update(
            AccountName("Pro"), new_name=AccountName("perso"), read_only=True, make_default=True
        )

    assert world.preferences.preferences == before


async def test_update_without_change_saves_nothing(world: World) -> None:
    await add(world, "Perso")
    saves = world.preferences.saves

    summary = await world.service.update(AccountName("Perso"), new_name=AccountName("Perso"))

    assert summary.name == AccountName("Perso")
    assert world.preferences.saves == saves


async def test_failed_removal_keeps_a_usable_account(world: World) -> None:
    await add(world, "Perso")
    account = await world.service.resolve()
    world.preferences.fail_on_save = True

    with pytest.raises(PreferencesUnavailableError):
        await world.service.remove(AccountName("Perso"))

    assert await world.service.resolve() == account
    assert world.secrets.tokens == {account.secret_key: SANDBOX_TOKEN}


async def test_allowing_writes_needs_a_confirmation_at_the_time_of_the_change(
    world: World,
) -> None:
    await add(world, "Perso")
    await world.service.set_read_only(AccountName("Perso"), True)

    with pytest.raises(WritesNotConfirmedError):
        await world.service.update(AccountName("Perso"), read_only=False)
    assert (await world.service.resolve()).read_only

    summary = await world.service.update(
        AccountName("Perso"), read_only=False, writes_confirmed=True
    )
    assert not summary.read_only


async def test_a_case_only_rename_is_saved(world: World) -> None:
    await add(world, "perso", "Pro")

    renamed = await world.service.rename(AccountName("perso"), AccountName("Perso"))

    assert str(renamed.name) == "Perso"
    assert [str(a.name) for a in await world.service.list()] == ["Perso", "Pro"]
    assert str(world.preferences.preferences.default_account) == "Perso"
