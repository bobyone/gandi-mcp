# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools buying: registration, renewal, restore and transfer in."""

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.registration_duration import RegistrationDuration
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.operations.domain.billable.register_domain import RegisterDomain
from gandi_mcp.operations.domain.billable.renew_domain import RenewDomain
from gandi_mcp.operations.domain.billable.restore_domain import RestoreDomain
from gandi_mcp.operations.domain.billable.transfer_in_domain import TransferInDomain
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.contact_parameter import ContactParameter
from gandi_mcp.protocol.tools.domains.domain_order_runner import (
    BILLABLE,
    ConfirmationIdParameter,
    DomainOrderRunner,
    DurationParameter,
    PayingOrganizationParameter,
)
from gandi_mcp.protocol.tools.domains.domain_tool_runner import AccountParameter, DomainParameter

ORDER_RULES = (
    " The price is checked with Gandi and shown to the user, who confirms outside the "
    "conversation; if the result is confirmation_pending, call again with the same "
    "arguments and the returned confirmation_id once the user answered."
)


def _contacts(
    owner: ContactParameter,
    admin: ContactParameter | None,
    tech: ContactParameter | None,
    bill: ContactParameter | None,
) -> DomainContacts:
    return DomainContacts(
        owner.to_contact(),
        admin.to_contact() if admin else None,
        tech.to_contact() if tech else None,
        bill.to_contact() if bill else None,
    )


class OrderTools(ToolModule):
    """``domain_register``, ``domain_renew``, ``domain_restore``, ``domain_transfer_in``."""

    def __init__(self, runner: DomainOrderRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_register,
                "domain_register",
                "Register a domain",
                "Buy a domain for a duration, with its owner (and optional admin, tech, "
                "billing) contacts, which only the user provides. Check the availability "
                "first with domain_check_availability.",
            ),
            (
                self.domain_renew,
                "domain_renew",
                "Renew a domain",
                "Renew a domain of the account for a duration.",
            ),
            (
                self.domain_restore,
                "domain_restore",
                "Restore a domain",
                "Restore an expired domain still in its restore period (see domain_restore_info).",
            ),
            (
                self.domain_transfer_in,
                "domain_transfer_in",
                "Transfer a domain to Gandi",
                "Start transferring a domain to Gandi, with its renewal duration and "
                "contacts. Never ask the user for the authorization code: they type it on "
                "the confirmation page. Check first with domain_transfer_in_check.",
            ),
        )
        for function, name, title, description in tools:
            server.add_tool(
                function,
                name=name,
                title=title,
                description=description + ORDER_RULES,
                annotations=BILLABLE,
            )

    async def domain_register(
        self,
        domain: DomainParameter,
        duration: DurationParameter,
        owner: ContactParameter,
        ctx: Context[Any, Any],
        *,
        admin: ContactParameter | None = None,
        tech: ContactParameter | None = None,
        bill: ContactParameter | None = None,
        paying_organization: PayingOrganizationParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Register a domain."""
        return await self._runner.order(
            ctx,
            lambda: RegisterDomain(
                DomainName(domain),
                RegistrationDuration(duration),
                _contacts(owner, admin, tech, bill),
            ),
            account,
            confirmation_id,
            paying_organization,
        )

    async def domain_renew(
        self,
        domain: DomainParameter,
        duration: DurationParameter,
        ctx: Context[Any, Any],
        *,
        paying_organization: PayingOrganizationParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Renew a domain."""
        return await self._runner.order(
            ctx,
            lambda: RenewDomain(DomainName(domain), RegistrationDuration(duration)),
            account,
            confirmation_id,
            paying_organization,
        )

    async def domain_restore(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        paying_organization: PayingOrganizationParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Restore a domain."""
        return await self._runner.order(
            ctx,
            lambda: RestoreDomain(DomainName(domain)),
            account,
            confirmation_id,
            paying_organization,
        )

    async def domain_transfer_in(
        self,
        domain: DomainParameter,
        duration: DurationParameter,
        owner: ContactParameter,
        ctx: Context[Any, Any],
        *,
        admin: ContactParameter | None = None,
        tech: ContactParameter | None = None,
        bill: ContactParameter | None = None,
        paying_organization: PayingOrganizationParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Transfer a domain to Gandi."""
        return await self._runner.order(
            ctx,
            lambda: TransferInDomain(
                DomainName(domain),
                RegistrationDuration(duration),
                _contacts(owner, admin, tech, bill),
            ),
            account,
            confirmation_id,
            paying_organization,
        )
