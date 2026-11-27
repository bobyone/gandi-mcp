# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Restore an expired domain (``POST /domain/domains/{domain}/restore``)."""

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
from gandi_mcp.operations.domain.billable.messages import RESTORE


class RestoreDomain(BillableOperation):
    """Restore a domain in its redemption period; no dry run, no price field."""

    def __init__(self, name: DomainName) -> None:
        self._name = name

    @property
    def name(self) -> str:
        return "domain_restore"

    @property
    def order_path(self) -> tuple[str, ...]:
        return ("domain", "domains", self._name.value, "restore")

    def parameters(self) -> Mapping[str, JsonValue]:
        return {"fqdn": self._name.value}

    def describe(self) -> LocalizedText:
        return LocalizedText(RESTORE, {"domain": self._name.unicode})

    def quote_request(self, paying_organization: OrganizationId | None) -> QuoteRequest:
        return QuoteRequest(
            self._name, DomainProcess.RESTORE, RegistrationDuration(1), paying_organization
        )

    def order_body(self, quote: Quote) -> JsonValue:
        return {}
