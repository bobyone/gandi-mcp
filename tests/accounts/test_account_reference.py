# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the binding of an account change to the account the user saw."""

import pytest

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_reference import AccountReference
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import AccountChangedError
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_sandbox_0123456789")
PRODUCTION = PersonalAccessToken("pat_production_01234567")
PERSO = AccountName("Perso")


def test_reference_follows_identity_and_environment() -> None:
    account = Account(PERSO, Environment.SANDBOX, False, "key-1")

    assert account.reference == AccountReference("key-1", Environment.SANDBOX)
    assert account.renamed(AccountName("Home")).reference == account.reference
    assert account.reference.fingerprint() == "key-1:sandbox"


@pytest.fixture
async def service() -> AccountService:
    verifier = StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, TOKEN)
    verifier.accept(Environment.PRODUCTION, PRODUCTION)
    accounts = AccountService(InMemoryPreferencesStore(), InMemorySecretStore(), verifier)
    await accounts.add(AccountDraft(PERSO, Environment.SANDBOX), TOKEN)
    return accounts


async def stale(service: AccountService) -> AccountReference:
    """A reference to the account, then replace the account under the same name."""
    reference = (await service.resolve(PERSO)).reference
    await service.remove(PERSO)
    await service.add(AccountDraft(PERSO, Environment.SANDBOX), TOKEN)
    return reference


async def test_changes_apply_to_the_expected_account(service: AccountService) -> None:
    reference = (await service.resolve(PERSO)).reference

    assert (await service.set_read_only(PERSO, True, reference)).read_only
    await service.remove(PERSO, reference)
    assert await service.list() == ()


async def test_a_replaced_account_does_not_match(service: AccountService) -> None:
    reference = await stale(service)

    with pytest.raises(AccountChangedError):
        await service.remove(PERSO, reference)
    with pytest.raises(AccountChangedError):
        await service.set_read_only(PERSO, True, reference)
    assert len(await service.list()) == 1


async def test_a_moved_account_does_not_match(service: AccountService) -> None:
    reference = (await service.resolve(PERSO)).reference
    await service.change_environment(PERSO, Environment.PRODUCTION, PRODUCTION)

    with pytest.raises(AccountChangedError):
        await service.remove(PERSO, reference)


async def test_token_changes_are_checked_before_calling_gandi(service: AccountService) -> None:
    reference = await stale(service)
    verifier = service._verifier  # test inspection of the double
    assert isinstance(verifier, StubTokenVerifier)
    calls = len(verifier.calls)

    with pytest.raises(AccountChangedError):
        await service.replace_token(PERSO, TOKEN, reference)
    with pytest.raises(AccountChangedError):
        await service.change_environment(PERSO, Environment.PRODUCTION, PRODUCTION, reference)
    assert len(verifier.calls) == calls


async def test_a_combined_update_checks_the_account_before_any_change(
    service: AccountService,
) -> None:
    reference = await stale(service)
    replacement = await service.resolve(PERSO)

    with pytest.raises(AccountChangedError):
        await service.update(
            PERSO, new_name=AccountName("Home"), read_only=True, expected=reference
        )

    assert await service.resolve(PERSO) == replacement
