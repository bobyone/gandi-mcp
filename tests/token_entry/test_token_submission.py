# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the application of a submitted token."""

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose
from gandi_mcp.token_entry.token_submission import TokenSubmission
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

pytestmark = pytest.mark.anyio

SANDBOX = PersonalAccessToken("pat_sandbox_0123456789")
OTHER = PersonalAccessToken("pat_other_0123456789ab")
PRODUCTION = PersonalAccessToken("pat_production_012345")


@pytest.fixture
def accounts() -> AccountService:
    verifier = StubTokenVerifier()
    for environment, token in [
        (Environment.SANDBOX, SANDBOX),
        (Environment.SANDBOX, OTHER),
        (Environment.PRODUCTION, PRODUCTION),
    ]:
        verifier.accept(environment, token)
    return AccountService(InMemoryPreferencesStore(), InMemorySecretStore(), verifier)


async def test_adds_an_account(accounts: AccountService) -> None:
    target = TokenEntryTarget(TokenPurpose.ADD, AccountName("Perso"), Environment.SANDBOX, True)

    verified = await TokenSubmission(accounts).submit(target, SANDBOX)

    assert verified.account.read_only
    assert verified.account.is_default


async def test_replaces_a_token(accounts: AccountService) -> None:
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), SANDBOX)
    target = TokenEntryTarget(TokenPurpose.REPLACE, AccountName("Perso"), Environment.SANDBOX)

    verified = await TokenSubmission(accounts).submit(target, OTHER)

    assert verified.account.name == AccountName("Perso")


async def test_changes_the_environment(accounts: AccountService) -> None:
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), SANDBOX)
    target = TokenEntryTarget(
        TokenPurpose.CHANGE_ENVIRONMENT, AccountName("Perso"), Environment.PRODUCTION
    )

    verified = await TokenSubmission(accounts).submit(target, PRODUCTION)

    assert verified.account.environment is Environment.PRODUCTION
