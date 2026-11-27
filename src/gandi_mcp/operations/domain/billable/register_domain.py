# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Register a domain (``POST /domain/domains``)."""

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
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.operations.domain.billable.messages import REGISTER
from gandi_mcp.operations.domain.billable.priced_body import price_fields


class RegisterDomain(BillableOperation):
    """Buy a domain for a duration, with its contacts; LiveDNS nameservers by default."""

    def __init__(
        self, name: DomainName, duration: RegistrationDuration, contacts: DomainContacts
    ) -> None:
        self._name = name
        self._duration = duration
        self._contacts = contacts

    @property
    def name(self) -> str:
        return "domain_register"

    @property
    def supports_dry_run(self) -> bool:
        return True

    @property
    def follow_up(self) -> str | None:
        return "domain_creation_status"

    @property
    def order_path(self) -> tuple[str, ...]:
        return ("domain", "domains")

    def parameters(self) -> Mapping[str, JsonValue]:
        return {
            "fqdn": self._name.value,
            "duration": self._duration.years,
            "contacts": dict(self._contacts.to_json()),
        }

    def describe(self) -> LocalizedText:
        return LocalizedText(
            REGISTER, {"domain": self._name.unicode, "count": self._duration.years}
        )

    def quote_request(self, paying_organization: OrganizationId | None) -> QuoteRequest:
        return QuoteRequest(self._name, DomainProcess.CREATE, self._duration, paying_organization)

    def order_body(self, quote: Quote) -> JsonValue:
        return {
            "fqdn": self._name.value,
            "duration": self._duration.years,
            **self._contacts.to_json(),
            **price_fields(quote),
        }
