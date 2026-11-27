# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools changing the contacts and the owner of a domain."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.exceptions import InvalidDomainInputError
from gandi_mcp.domains.write_values import EmailAddress
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.domain.billable.domain_contacts import DomainContacts
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.contact_parameter import ContactParameter
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    DomainParameter,
    DomainToolRunner,
    add_write_tool,
)

# Gandi does not accept these fields when editing the owner: they cannot change.
FIXED_OWNER_FIELDS = frozenset({"type", "orgname"})
EmailParameter = Annotated[
    str, Field(description="Email address to send the confirmation email to.", max_length=254)
]


class ContactTools(ToolModule):
    """Admin, tech and billing contacts, owner details and owner change."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_contacts_update,
                domain_endpoints.CONTACTS_UPDATE,
                "Update the contacts of a domain",
                "Replace the admin, tech and/or billing contact of a domain with details the "
                "user provides.",
            ),
            (
                self.domain_owner_update,
                domain_endpoints.OWNER_UPDATE,
                "Update the owner details of a domain",
                "Correct the details of the current owner (address, phone); the owner stays "
                "the same person or organization. Keep the current email address: use "
                "domain_owner_email_update to change it. Checked by Gandi first.",
            ),
            (
                self.domain_owner_email_update,
                domain_endpoints.OWNER_EMAIL_UPDATE,
                "Update the owner details of a domain, including its email",
                "Correct the details of the current owner, including its email address. The "
                "user authorizes Gandi to act as their Designated Agent under the ICANN rules "
                "by confirming outside the conversation.",
            ),
            (
                self.domain_owner_change,
                domain_endpoints.OWNER_CHANGE,
                "Give a domain to a new owner",
                "Start giving a domain to a new owner, whose details the user provides. "
                "Gandi may charge for it depending on the extension. Checked by Gandi first; "
                "follow it with domain_owner_change_status.",
            ),
            (
                self.domain_owner_change_resend,
                domain_endpoints.OWNER_CHANGE_RESEND,
                "Resend the owner change emails",
                "Resend the emails asking the old and new owners to approve an owner change.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_contacts_update(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        *,
        admin: ContactParameter | None = None,
        tech: ContactParameter | None = None,
        bill: ContactParameter | None = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Update the admin, tech and billing contacts."""

        def body() -> JsonValue:
            given = {"admin": admin, "tech": tech, "bill": bill}
            contacts: dict[str, JsonValue] = {
                role: contact.to_contact().to_json() for role, contact in given.items() if contact
            }
            if not contacts:
                raise InvalidDomainInputError("give at least one contact to update")
            return contacts

        return await self._runner.write(
            ctx,
            domain_endpoints.CONTACTS_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
        )

    async def domain_owner_update(
        self,
        domain: DomainParameter,
        owner: ContactParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Update the details of the owner."""

        def body() -> JsonValue:
            fields = owner.to_contact().to_json()
            return {key: value for key, value in fields.items() if key not in FIXED_OWNER_FIELDS}

        return await self._runner.write(
            ctx,
            domain_endpoints.OWNER_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )

    async def domain_owner_email_update(
        self,
        domain: DomainParameter,
        owner: ContactParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Update the owner details, email included, with the designated-agent consent."""

        def body() -> JsonValue:
            fields = owner.to_contact().to_json()
            kept = {key: value for key, value in fields.items() if key not in FIXED_OWNER_FIELDS}
            # The consent is given by the user's confirmation, whose text states it.
            return {**kept, "icann_contract_accept": True}

        return await self._runner.write(
            ctx,
            domain_endpoints.OWNER_EMAIL_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )

    async def domain_owner_change(
        self,
        domain: DomainParameter,
        owner: ContactParameter,
        ctx: Context[Any, Any],
        *,
        admin: ContactParameter | None = None,
        tech: ContactParameter | None = None,
        bill: ContactParameter | None = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Give a domain to a new owner."""

        def body() -> JsonValue:
            contacts = DomainContacts(
                owner.to_contact(),
                admin.to_contact() if admin else None,
                tech.to_contact() if tech else None,
                bill.to_contact() if bill else None,
            )
            return dict(contacts.to_json())

        return await self._runner.write(
            ctx,
            domain_endpoints.OWNER_CHANGE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )

    async def domain_owner_change_resend(
        self,
        domain: DomainParameter,
        email: EmailParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Resend the owner change emails."""
        return await self._runner.write(
            ctx,
            domain_endpoints.OWNER_CHANGE_RESEND,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=lambda: {"email": EmailAddress(email).value},
        )
