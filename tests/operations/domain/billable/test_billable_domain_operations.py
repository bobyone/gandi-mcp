# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the concrete orders: requests, bodies and descriptions."""

from decimal import Decimal

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.contacts.domain_contact import ContactType, DomainContact
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.money import Money
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.operations.domain.billable.register_domain import RegisterDomain
from gandi_mcp.operations.domain.billable.renew_domain import RenewDomain
from gandi_mcp.operations.domain.billable.restore_domain import RestoreDomain
from gandi_mcp.operations.domain.billable.transfer_in_domain import TransferInDomain
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
ORG = OrganizationId("5a53edc7-b514-416a-98c2-2d477a288eb9")
NAME = DomainName("bücher.fr")
OWNER = DomainContact(
    ContactType.INDIVIDUAL,
    "Ada",
    "Lovelace",
    "ada@example.org",
    "1 rue de Paris",
    "Paris",
    "75001",
    "FR",
)
CONTACTS = DomainContacts(OWNER, tech=OWNER)


def quote(
    operation: RegisterDomain | TransferInDomain | RenewDomain | RestoreDomain,
    premium: bool = False,
) -> Quote:
    return Quote(
        operation.quote_request(ORG),
        Money(Decimal("24.00"), "EUR"),
        Money(Decimal("20.00"), "EUR"),
        premium=premium,
    )


async def test_registration() -> None:
    operation = RegisterDomain(NAME, RegistrationDuration(2), CONTACTS)
    client = FakeGandiClient()

    await operation.order(client, Environment.SANDBOX, TOKEN, quote(operation, True), dry_run=True)

    call = client.calls[0]
    assert (call.method, call.path, call.query, call.dry_run) == (
        "POST",
        ("domain", "domains"),
        {"sharing_id": str(ORG)},
        True,
    )
    assert call.body == {
        "fqdn": "xn--bcher-kva.fr",
        "duration": 2,
        "owner": OWNER.to_json(),
        "tech": OWNER.to_json(),
        "price": 20.0,
        "currency": "EUR",
        "enforce_premium": True,
    }
    assert operation.category is OperationCategory.BILLABLE
    assert operation.supports_dry_run
    assert operation.follow_up == "domain_creation_status"
    assert operation.quote_request(None).process is DomainProcess.CREATE
    assert operation.describe().params == {"domain": "bücher.fr", "count": 2}
    assert operation.secret_input() is None


async def test_renewal_and_restore() -> None:
    renew = RenewDomain(NAME, RegistrationDuration(3))
    restore = RestoreDomain(NAME)
    client = FakeGandiClient()

    await renew.order(client, Environment.SANDBOX, TOKEN, quote(renew))
    await restore.order(client, Environment.SANDBOX, TOKEN, quote(restore))

    assert client.calls[0].path == ("domain", "domains", "xn--bcher-kva.fr", "renew")
    assert client.calls[0].body == {"duration": 3}
    assert client.calls[1].path == ("domain", "domains", "xn--bcher-kva.fr", "restore")
    assert client.calls[1].body == {}
    assert restore.quote_request(None).duration.years == 1
    assert not restore.supports_dry_run
    assert renew.parameters() == {"fqdn": "xn--bcher-kva.fr", "duration": 3}


async def test_transfer_carries_the_typed_code_only() -> None:
    operation = TransferInDomain(NAME, RegistrationDuration(1), DomainContacts(OWNER))
    client = FakeGandiClient()

    await operation.order(
        client, Environment.SANDBOX, TOKEN, quote(operation), secret=SecretValue("Auth-123")
    )

    body = client.calls[0].body
    assert isinstance(body, dict)
    assert body["authinfo"] == "Auth-123"
    assert client.calls[0].path == ("domain", "transferin")
    assert "Auth-123" not in operation.subject()
    assert operation.secret_input().max_length == 128
    assert not operation.supports_dry_run
    assert operation.with_secret(["x"], SecretValue("a")) == ["x"]


async def test_billable_operations_only_run_as_orders() -> None:
    with pytest.raises(TypeError, match="OrderExecutor"):
        await RestoreDomain(NAME).execute(FakeGandiClient(), Environment.SANDBOX, TOKEN)
