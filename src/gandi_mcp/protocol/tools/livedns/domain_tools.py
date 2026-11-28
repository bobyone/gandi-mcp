# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools on the record types, the LiveDNS domains and their nameservers."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
    add_write_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    RecordParameter,
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
        add_write_tool(
            server,
            self.livedns_domain_add,
            livedns_endpoints.DOMAIN_ADD,
            "Add a domain to LiveDNS",
            "Create the LiveDNS zone of a domain of the account, optionally with its first "
            "records; it does not change the nameservers of the domain "
            "(domain_livedns_enable does).",
        )
        add_write_tool(
            server,
            self.livedns_automatic_snapshots_update,
            livedns_endpoints.AUTOMATIC_SNAPSHOTS_UPDATE,
            "Turn the automatic snapshots of a zone on or off",
            "Turn on or off the snapshot LiveDNS takes after each change of a zone.",
        )

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

    async def livedns_domain_add(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        *,
        records: Annotated[
            list[RecordParameter] | None,
            Field(default=None, description="First records of the zone.", max_length=1000),
        ] = None,
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Add a domain to LiveDNS."""

        def body() -> dict[str, Any]:
            fields: dict[str, Any] = {"fqdn": DomainName(domain).value}
            if records:
                fields["zone"] = {"items": [record.record().to_json() for record in records]}
            return fields

        return await self._runner.write(
            ctx,
            livedns_endpoints.DOMAIN_ADD,
            account,
            dict,
            body=body,
            query=lambda: {"sharing_id": sharing_id(organization_id)},
        )

    async def livedns_automatic_snapshots_update(
        self,
        domain: LiveDnsDomainParameter,
        enabled: Annotated[
            bool, Field(description="True to turn them on, false to turn them off.")
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Turn the automatic snapshots of a zone on or off."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.AUTOMATIC_SNAPSHOTS_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=lambda: {"automatic_snapshots": enabled},
        )
