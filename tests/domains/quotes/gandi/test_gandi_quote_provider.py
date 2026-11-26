# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the quotes from ``/domain/check``, with documented answers."""

from decimal import Decimal

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.money import Money
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.quotes.exceptions import (
    NoPriceForDurationError,
    NotAvailableError,
    QuoteUnavailableError,
)
from gandi_mcp.domains.quotes.gandi.gandi_quote_provider import GandiQuoteProvider
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
ORG = OrganizationId("5a53edc7-b514-416a-98c2-2d477a288eb9")
# "Availability and price, with processes and price rate" (Gandi documentation).
DOCUMENTED: JsonValue = {
    "currency": "EUR",
    "grid": "C",
    "products": [
        {
            "status": "available",
            "name": "example.com",
            "process": "transfer",
            "prices": [
                {
                    "max_duration": 1,
                    "duration_unit": "y",
                    "min_duration": 1,
                    "discount": False,
                    "price_after_taxes": 7.2,
                    "price_before_taxes": 6,
                }
            ],
        },
        {
            "status": "available",
            "name": "example.com",
            "process": "create",
            "prices": [
                {
                    "max_duration": 2,
                    "duration_unit": "y",
                    "min_duration": 1,
                    "discount": True,
                    "price_after_taxes": 5.52,
                    "price_before_taxes": 4.6,
                },
                {
                    "max_duration": 10,
                    "duration_unit": "y",
                    "min_duration": 3,
                    "discount": True,
                    "price_after_taxes": 4.69,
                    "price_before_taxes": 3.91,
                },
            ],
        },
    ],
}


def request(
    process: DomainProcess = DomainProcess.CREATE,
    years: int = 1,
    organization: OrganizationId | None = None,
) -> QuoteRequest:
    return QuoteRequest(
        DomainName("example.com"), process, RegistrationDuration(years), organization
    )


async def quote(data: JsonValue, wanted: QuoteRequest) -> tuple[object, FakeGandiClient]:
    client = FakeGandiClient([GandiResponse(200, data)])
    result = await GandiQuoteProvider(client).quote(Environment.SANDBOX, TOKEN, wanted)
    return result, client


async def test_prices_the_requested_process_and_duration_band() -> None:
    result, client = await quote(DOCUMENTED, request(years=3, organization=ORG))

    assert result.price == Money(Decimal("14.07"), "EUR")  # type: ignore[attr-defined]
    assert result.price_before_taxes == Money(Decimal("11.73"), "EUR")  # type: ignore[attr-defined]
    assert result.discount  # type: ignore[attr-defined]
    assert not result.premium  # type: ignore[attr-defined]
    assert client.calls[0].query == {
        "name": "example.com",
        "processes": ["create"],
        "sharing_id": str(ORG),
    }


async def test_transfer_status_is_not_an_availability() -> None:
    data: JsonValue = {
        "currency": "EUR",
        "products": [
            {
                "status": "unavailable",
                "process": "transfer",
                "prices": [
                    {
                        "min_duration": 1,
                        "max_duration": 1,
                        "price_after_taxes": 7.2,
                        "price_before_taxes": 6,
                        "type": "premium",
                    }
                ],
            }
        ],
    }

    result, client = await quote(data, request(DomainProcess.TRANSFER))

    assert result.price == Money(Decimal("7.2"), "EUR")  # type: ignore[attr-defined]
    assert result.premium  # type: ignore[attr-defined]
    assert "sharing_id" not in (client.calls[0].query or {})


@pytest.mark.parametrize("status", ["unavailable", "unavailable_premium", "reserved_corporate"])
async def test_an_unavailable_domain_is_refused(status: str) -> None:
    data: JsonValue = {"currency": "EUR", "products": [{"status": status, "process": "create"}]}

    with pytest.raises(NotAvailableError) as raised:
        await quote(data, request())

    assert raised.value.status == status


@pytest.mark.parametrize(
    "data",
    [
        {"currency": "EUR", "grid": "A"},
        {"currency": "EUR", "products": []},
        {"currency": "EUR", "products": [{"status": "pending", "process": "create"}]},
        {"currency": "EUR", "products": [{"status": "available", "process": "renew"}]},
    ],
)
async def test_missing_or_pending_prices_are_not_ready(data: JsonValue) -> None:
    with pytest.raises(QuoteUnavailableError):
        await quote(data, request())


async def test_no_price_for_this_duration() -> None:
    with pytest.raises(NoPriceForDurationError):
        await quote(DOCUMENTED, request(DomainProcess.TRANSFER, years=2))


async def test_single_product_without_process() -> None:
    data: JsonValue = {
        "currency": "USD",
        "products": [
            {
                "status": "available",
                "prices": [
                    {
                        "min_duration": 1,
                        "max_duration": 10,
                        "price_after_taxes": "10.00",
                        "price_before_taxes": "8.00",
                    }
                ],
            }
        ],
    }

    result, _client = await quote(data, request(years=2))

    assert result.price == Money(Decimal("20.00"), "USD")  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "data",
    [
        {"products": DOCUMENTED["products"]},  # type: ignore[index,call-overload]
        {"currency": "EUROS", "products": DOCUMENTED["products"]},  # type: ignore[index,call-overload]
        {
            "currency": "EUR",
            "products": [
                {
                    "status": "available",
                    "process": "create",
                    "prices": [
                        {
                            "min_duration": 1,
                            "max_duration": 1,
                            "price_after_taxes": "free",
                            "price_before_taxes": 1,
                        }
                    ],
                }
            ],
        },
        {
            "currency": "EUR",
            "products": [
                {
                    "status": "available",
                    "process": "create",
                    "prices": [
                        {
                            "min_duration": 1,
                            "max_duration": 1,
                            "price_after_taxes": True,
                            "price_before_taxes": 1,
                        }
                    ],
                }
            ],
        },
        {
            "currency": "EUR",
            "products": [
                {
                    "status": "available",
                    "process": "create",
                    "prices": [
                        {
                            "min_duration": 1,
                            "max_duration": 1,
                            "price_after_taxes": -1,
                            "price_before_taxes": 1,
                        }
                    ],
                }
            ],
        },
    ],
)
async def test_unexpected_answers(data: JsonValue) -> None:
    with pytest.raises(GandiUnexpectedResponseError):
        await quote(data, request())
