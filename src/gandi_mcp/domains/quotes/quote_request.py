# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of what to price."""

from dataclasses import dataclass

from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.quotes.domain_process import DomainProcess
from gandi_mcp.domains.registration_duration import RegistrationDuration


@dataclass(frozen=True)
class QuoteRequest:
    """A domain, a process, a duration and the organization that would pay."""

    name: DomainName
    process: DomainProcess
    duration: RegistrationDuration
    paying_organization: OrganizationId | None = None
