# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Transfer a domain to Gandi (``POST /domain/transferin``)."""

from collections.abc import Mapping

from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.operations.billable_operation import BillableOperation
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.operations.domain.billable.messages import AUTHORIZATION_CODE, TRANSFER_IN
from gandi_mcp.operations.domain.billable.priced_body import price_fields
from gandi_mcp.secrets.secret_value import SecretValue

MAX_AUTHORIZATION_CODE_LENGTH = 128


class TransferInDomain(BillableOperation):
    """Start the transfer of a domain to Gandi, with its renewal duration and contacts.

    The authorization code is typed by the user in the confirmation (ADR 11), never
    passed through the model. No dry run: it would run before the code is known.
    """

    def __init__(
        self, name: DomainName, duration: RegistrationDuration, contacts: DomainContacts
    ) -> None:
        self._name = name
        self._duration = duration
        self._contacts = contacts

    @property
    def name(self) -> str:
        return "domain_transfer_in"

    @property
    def follow_up(self) -> str | None:
        return "domain_transfer_in_status"

    @property
    def order_path(self) -> tuple[str, ...]:
        return ("domain", "transferin")

    def secret_input(self) -> SecretInput:
        return SecretInput(AUTHORIZATION_CODE, MAX_AUTHORIZATION_CODE_LENGTH)

    def parameters(self) -> Mapping[str, JsonValue]:
        return {
            "fqdn": self._name.value,
            "duration": self._duration.years,
            "contacts": dict(self._contacts.to_json()),
        }

    def describe(self) -> LocalizedText:
        return LocalizedText(
            TRANSFER_IN, {"domain": self._name.unicode, "count": self._duration.years}
        )

    def quote_request(self, paying_organization: OrganizationId | None) -> QuoteRequest:
        return QuoteRequest(self._name, DomainProcess.TRANSFER, self._duration, paying_organization)

    def order_body(self, quote: Quote) -> JsonValue:
        return {
            "fqdn": self._name.value,
            "duration": self._duration.years,
            **self._contacts.to_json(),
            **price_fields(quote),
        }

    def with_secret(self, body: JsonValue, secret: SecretValue | None) -> JsonValue:
        if secret is None or not isinstance(body, dict):
            return body
        return {**body, "authinfo": secret.reveal()}
