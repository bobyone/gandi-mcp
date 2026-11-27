# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Quotes from the Gandi availability endpoint (``GET /domain/check``)."""

from decimal import Decimal, InvalidOperation

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.domains.exceptions import InvalidDomainInputError
from gandi_mcp.domains.money import Money
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.quotes.exceptions import (
    AmbiguousPriceError,
    NoPriceForDurationError,
    NotAvailableError,
    QuoteUnavailableError,
)
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_provider import QuoteProvider
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import GandiClient, QueryValue
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

CHECK_PATH = ("domain", "check")
AVAILABLE = frozenset({"available", "available_reserved", "available_preorder"})
NOT_READY = frozenset({"pending", "error_refused", "error_timeout", "error_unknown"})
YEAR = "y"
PREMIUM = "premium"


def _amount(value: JsonValue) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise GandiUnexpectedResponseError("Gandi returned a price that is not a number")
    try:
        return Decimal(str(value))
    except InvalidOperation as error:
        raise GandiUnexpectedResponseError("Gandi returned an invalid price") from error


def _product(data: JsonValue, process: DomainProcess) -> dict[str, JsonValue]:
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(products, list) or not products:
        raise QuoteUnavailableError("Gandi returned no price yet")
    candidates = [item for item in products if isinstance(item, dict)]
    for product in candidates:
        if product.get("process") == process.value:
            return product
    if len(candidates) == 1 and candidates[0].get("process") is None:
        return candidates[0]
    raise QuoteUnavailableError(f"Gandi returned no price for {process.value}")


def _band(product: dict[str, JsonValue], years: int) -> dict[str, JsonValue]:
    """The one price band of the duration.

    Several bands with different prices match during registration phases (early
    access, sunrise...); the applicable one cannot be told apart, so the quote is
    refused rather than guessed.
    """
    prices = product.get("prices")
    matching: list[dict[str, JsonValue]] = []
    for band in prices if isinstance(prices, list) else []:
        if not isinstance(band, dict) or band.get("duration_unit", YEAR) != YEAR:
            continue
        low, high = band.get("min_duration"), band.get("max_duration")
        if isinstance(low, int) and isinstance(high, int) and low <= years <= high:
            matching.append(band)
    if not matching:
        raise NoPriceForDurationError(f"no price for {years} years")
    amounts = {
        (_amount(band.get("price_after_taxes")), _amount(band.get("price_before_taxes")))
        for band in matching
    }
    if len(amounts) > 1:
        raise AmbiguousPriceError(f"{len(amounts)} different prices for {years} years")
    return matching[0]


class GandiQuoteProvider(QuoteProvider):
    """Price with ``GET /domain/check`` for one process and the paying organization.

    The availability status is only checked for a registration (Gandi says to ignore
    it for the other processes). A band price is per year: the quote multiplies it
    by the duration. A missing product or a pending status means "not ready yet".
    """

    def __init__(self, client: GandiClient) -> None:
        self._client = client

    async def quote(
        self, environment: Environment, token: PersonalAccessToken, request: QuoteRequest
    ) -> Quote:
        query: dict[str, QueryValue] = {
            "name": request.name.value,
            "processes": [request.process.value],
        }
        if request.paying_organization is not None:
            query["sharing_id"] = str(request.paying_organization)
        response = await self._client.request(environment, token, "GET", CHECK_PATH, query=query)
        product = _product(response.data, request.process)
        status = product.get("status")
        if request.process is DomainProcess.CREATE:
            if status in NOT_READY:
                raise QuoteUnavailableError("Gandi could not check the availability yet")
            if status not in AVAILABLE:
                raise NotAvailableError("the domain is not available", str(status))
        band = _band(product, request.duration.years)
        currency = response.data.get("currency") if isinstance(response.data, dict) else None
        if not isinstance(currency, str):
            raise GandiUnexpectedResponseError("Gandi returned no currency")
        years = Decimal(request.duration.years)
        try:
            price = Money(_amount(band.get("price_after_taxes")) * years, currency)
            before = Money(_amount(band.get("price_before_taxes")) * years, currency)
        except InvalidDomainInputError as error:
            raise GandiUnexpectedResponseError("Gandi returned an invalid price") from error
        return Quote(
            request,
            price,
            before,
            premium=band.get("type") == PREMIUM,
            discount=band.get("discount") is True,
        )
