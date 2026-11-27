# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the record types, the LiveDNS domains and their nameservers."""

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    SharingIdParameter,
    sharing_id,
)


class LiveDnsDomainTools(ToolModule):
    """Record types, LiveDNS domains and the nameservers of their zones."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.livedns_record_types,
                livedns_endpoints.RECORD_TYPES,
                "List the DNS record types",
                "List the record types LiveDNS accepts.",
            ),
            (
                self.livedns_domains,
                livedns_endpoints.DOMAINS,
                "List the LiveDNS domains",
                "List the domains whose zone is served by LiveDNS.",
            ),
            (
                self.livedns_domain,
                livedns_endpoints.DOMAIN_DETAILS,
                "Show a LiveDNS domain",
                "Show a LiveDNS domain and whether its automatic snapshots are on.",
            ),
            (
                self.livedns_nameservers,
                livedns_endpoints.NAMESERVERS,
                "List the nameservers of a zone",
                "List the nameservers LiveDNS gives the zone of a domain.",
            ),
            (
                self.livedns_public_nameservers,
                livedns_endpoints.PUBLIC_NAMESERVERS,
                "Compute the LiveDNS nameservers of any name",
                "Give the LiveDNS nameservers any domain would get, even one not in the "
                "account; use livedns_nameservers for a zone with its own NS records.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_read_tool(server, function, endpoint, title, description)

    async def livedns_record_types(
        self, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """List the DNS record types."""
        return await self._runner.read(ctx, livedns_endpoints.RECORD_TYPES, account)

    async def livedns_domains(
        self,
        ctx: Context[Any, Any],
        *,
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the LiveDNS domains."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.DOMAINS,
            account,
            query=lambda: {"sharing_id": sharing_id(organization_id)},
            page=(page, per_page),
        )

    async def livedns_domain(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Show a LiveDNS domain."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.DOMAIN_DETAILS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )

    async def livedns_nameservers(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the nameservers of a zone."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.NAMESERVERS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )

    async def livedns_public_nameservers(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Compute the LiveDNS nameservers of any name."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.PUBLIC_NAMESERVERS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )
