# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Renew a domain (``POST /domain/domains/{domain}/renew``)."""

from collections.abc import Mapping

from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.operations.billable_operation import BillableOperation
from gandi_mcp.operations.domain.billable.messages import RENEW


class RenewDomain(BillableOperation):
    """Extend a domain for a duration; Gandi accepts no price field for a renewal."""

    def __init__(self, name: DomainName, duration: RegistrationDuration) -> None:
        self._name = name
        self._duration = duration

    @property
    def name(self) -> str:
        return "domain_renew"

    @property
    def supports_dry_run(self) -> bool:
        return True

    @property
    def order_path(self) -> tuple[str, ...]:
        return ("domain", "domains", self._name.value, "renew")

    def parameters(self) -> Mapping[str, JsonValue]:
        return {"fqdn": self._name.value, "duration": self._duration.years}

    def describe(self) -> LocalizedText:
        return LocalizedText(RENEW, {"domain": self._name.unicode, "count": self._duration.years})

    def quote_request(self, paying_organization: OrganizationId | None) -> QuoteRequest:
        return QuoteRequest(self._name, DomainProcess.RENEW, self._duration, paying_organization)

    def order_body(self, quote: Quote) -> JsonValue:
        return {"duration": self._duration.years}
