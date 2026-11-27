# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the organizations of an account and its paying organization."""

from dataclasses import dataclass, field

import pytest

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import UnknownOrganizationError
from gandi_mcp.accounts.organization import Organization
from gandi_mcp.accounts.organization_directory import OrganizationDirectory
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.accounts.organization_service import OrganizationService
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_preferences_store import InMemoryPreferencesStore
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

ORG_ID = "5a53edc7-b514-416a-98c2-2d477a288eb9"
OTHER_ID = "0b1c2d3e-4f50-4617-8899-aabbccddeeff"
pytestmark = pytest.mark.anyio

SANDBOX = PersonalAccessToken("pat_sandbox_0123456789")
PRODUCTION = PersonalAccessToken("pat_production_0123456789")
ORG = OrganizationId(ORG_ID)


@dataclass
class StubDirectory(OrganizationDirectory):
    found: tuple[Organization, ...] = (Organization(ORG, "Ada Corp", "company"),)
    calls: list[tuple[Environment, PersonalAccessToken]] = field(default_factory=list)

    async def organizations(
        self, environment: Environment, token: PersonalAccessToken
    ) -> tuple[Organization, ...]:
        self.calls.append((environment, token))
        return self.found


@dataclass
class World:
    accounts: AccountService
    directory: StubDirectory
    service: OrganizationService


@pytest.fixture
async def world() -> World:
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, SANDBOX)
    verifier.accept(Environment.PRODUCTION, PRODUCTION)
    accounts = AccountService(InMemoryPreferencesStore(), secrets, verifier)
    await accounts.add(AccountDraft(AccountName("Perso"), Environment.SANDBOX), SANDBOX)
    directory = StubDirectory()
    return World(accounts, directory, OrganizationService(accounts, secrets, directory))


async def test_lists_with_the_account_token(world: World) -> None:
    found = await world.service.organizations(None)

    assert found == world.directory.found
    assert world.directory.calls == [(Environment.SANDBOX, SANDBOX)]


async def test_sets_and_clears_the_paying_organization(world: World) -> None:
    chosen = await world.service.set_paying_organization(AccountName("Perso"), ORG)
    cleared = await world.service.set_paying_organization(None, None)

    assert chosen.paying_organization == ORG
    assert cleared.paying_organization is None
    assert len(world.directory.calls) == 1  # clearing needs no check


async def test_refuses_an_organization_of_someone_else(world: World) -> None:
    with pytest.raises(UnknownOrganizationError):
        await world.service.set_paying_organization(None, OrganizationId(OTHER_ID))

    assert (await world.accounts.resolve()).paying_organization is None


async def test_moving_to_another_environment_drops_the_choice(world: World) -> None:
    await world.service.set_paying_organization(None, ORG)

    moved = await world.accounts.change_environment(
        AccountName("Perso"), Environment.PRODUCTION, PRODUCTION
    )

    assert moved.account.paying_organization is None
