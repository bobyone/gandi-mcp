# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the domains of an account and their information."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName, TldName
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    AuthorizationCodeParameter,
    ContactDetailsParameter,
    DomainParameter,
    DomainToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
)

FQDN_PATTERN = r"^[\w.*-]+$"


class DomainsTools(ToolModule):
    """The domains of an account, their details, contacts and information."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_read_tool(
            server,
            self.domain_list,
            domain_endpoints.LIST_DOMAINS,
            "List the domains",
            "List the domains of the account, with their expiry dates and status.",
        )
        add_read_tool(
            server,
            self.domain_details,
            domain_endpoints.DETAILS,
            "Describe a domain",
            "Describe a domain: dates, status, nameservers, automatic renewal, transfer "
            "lock. Contact details and the authorization code are hidden unless asked.",
        )
        add_read_tool(
            server,
            self.domain_contacts,
            domain_endpoints.CONTACTS,
            "Show the contacts of a domain",
            "Show the owner, admin, tech and billing contacts of a domain. Only their type "
            "and country unless the full details are asked.",
        )
        simple = (
            (
                self.domain_creation_status,
                domain_endpoints.CREATION_STATUS,
                "Follow the registration of a domain",
                "Show the progress of a domain registration after its order.",
            ),
            (
                self.domain_tags,
                domain_endpoints.TAGS,
                "List the tags of a domain",
                "List the tags attached to a domain.",
            ),
            (
                self.domain_renewal_info,
                domain_endpoints.RENEWAL_INFO,
                "Show the renewal information of a domain",
                "Show whether a domain can be renewed, until when, for which durations and prices.",
            ),
            (
                self.domain_restore_info,
                domain_endpoints.RESTORE_INFO,
                "Show the restore information of a domain",
                "Show whether an expired domain can be restored, until when and at which price.",
            ),
            (
                self.domain_claims,
                domain_endpoints.CLAIMS,
                "Show the trademark claims of a domain",
                "Show the trademark claims notified for a domain.",
            ),
        )
        for function, endpoint, title, description in simple:
            add_read_tool(server, function, endpoint, title, description)

    async def domain_list(
        self,
        ctx: Context[Any, Any],
        *,
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        fqdn: Annotated[
            str | None,
            Field(
                default=None,
                description="Filter on the name, with * as a wildcard, e.g. example.* or *.fr.",
                max_length=253,
                pattern=FQDN_PATTERN,
            ),
        ] = None,
        tld: Annotated[
            str | None, Field(default=None, description="Only this extension.", max_length=63)
        ] = None,
        nameserver: Annotated[
            Literal["abc", "livedns", "other"] | None,
            Field(default=None, description="Only domains using these nameservers."),
        ] = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the domains of the account."""
        return await self._runner.read(
            ctx,
            domain_endpoints.LIST_DOMAINS,
            account,
            query=lambda: {
                "fqdn": fqdn,
                "tld": TldName(tld).value if tld is not None else None,
                "nameserver": nameserver,
            },
            page=(page, per_page),
        )

    async def domain_details(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        include_contact_details: ContactDetailsParameter = False,
        include_authorization_code: AuthorizationCodeParameter = False,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Describe a domain."""
        return await self._runner.read(
            ctx,
            domain_endpoints.DETAILS,
            account,
            lambda: {"domain": DomainName(domain).value},
            include_contact_details=include_contact_details,
            include_authorization_code=include_authorization_code,
        )

    async def domain_contacts(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        include_contact_details: ContactDetailsParameter = False,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Show the contacts of a domain."""
        return await self._runner.read(
            ctx,
            domain_endpoints.CONTACTS,
            account,
            lambda: {"domain": DomainName(domain).value},
            include_contact_details=include_contact_details,
        )

    async def domain_creation_status(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Follow the registration of a domain."""
        return await self._read(ctx, domain_endpoints.CREATION_STATUS, domain, account)

    async def domain_tags(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """List the tags of a domain."""
        return await self._read(ctx, domain_endpoints.TAGS, domain, account)

    async def domain_renewal_info(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Show the renewal information of a domain."""
        return await self._read(ctx, domain_endpoints.RENEWAL_INFO, domain, account)

    async def domain_restore_info(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Show the restore information of a domain."""
        return await self._read(ctx, domain_endpoints.RESTORE_INFO, domain, account)

    async def domain_claims(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Show the trademark claims of a domain."""
        return await self._read(ctx, domain_endpoints.CLAIMS, domain, account)

    async def _read(
        self, ctx: Context[Any, Any], endpoint: DomainEndpoint, domain: str, account: str | None
    ) -> dict[str, Any]:
        return await self._runner.read(
            ctx, endpoint, account, lambda: {"domain": DomainName(domain).value}
        )
