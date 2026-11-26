# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the nameservers, LiveDNS, DNSSEC and glue records of a domain."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName, HostLabel
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    DomainParameter,
    DomainToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
)


class NameserverTools(ToolModule):
    """Nameservers, LiveDNS, DNSSEC keys and glue records."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_nameservers,
                domain_endpoints.NAMESERVERS,
                "List the nameservers of a domain",
                "List the nameservers a domain is delegated to.",
            ),
            (
                self.domain_livedns_status,
                domain_endpoints.LIVEDNS_STATUS,
                "Show the LiveDNS status of a domain",
                "Show whether a domain uses the Gandi LiveDNS nameservers.",
            ),
            (
                self.domain_dnssec_status,
                domain_endpoints.DNSSEC_STATUS,
                "Show the DNSSEC status of a domain",
                "Show whether DNSSEC is enabled through LiveDNS for a domain.",
            ),
            (
                self.domain_dnssec_keys,
                domain_endpoints.DNSSEC_KEYS,
                "List the DNSSEC keys of a domain",
                "List the DNSSEC keys published at the registry for a domain.",
            ),
            (
                self.domain_glue_records,
                domain_endpoints.GLUE_RECORDS,
                "List the glue records of a domain",
                "List the glue records (nameservers named under the domain, with their IP "
                "addresses).",
            ),
            (
                self.domain_glue_record,
                domain_endpoints.GLUE_RECORD,
                "Describe a glue record",
                "Describe one glue record of a domain and its IP addresses.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_read_tool(server, function, endpoint, title, description)

    async def domain_nameservers(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """List the nameservers of a domain."""
        return await self._read(ctx, domain_endpoints.NAMESERVERS, domain, account)

    async def domain_livedns_status(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Show the LiveDNS status of a domain."""
        return await self._read(ctx, domain_endpoints.LIVEDNS_STATUS, domain, account)

    async def domain_dnssec_status(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Show the DNSSEC status of a domain."""
        return await self._read(ctx, domain_endpoints.DNSSEC_STATUS, domain, account)

    async def domain_dnssec_keys(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the DNSSEC keys of a domain."""
        return await self._read(
            ctx, domain_endpoints.DNSSEC_KEYS, domain, account, page=(page, per_page)
        )

    async def domain_glue_records(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the glue records of a domain."""
        return await self._read(
            ctx, domain_endpoints.GLUE_RECORDS, domain, account, page=(page, per_page)
        )

    async def domain_glue_record(
        self,
        domain: DomainParameter,
        host: Annotated[
            str, Field(description="Host name under the domain, e.g. ns1.", max_length=253)
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Describe a glue record."""
        return await self._runner.read(
            ctx,
            domain_endpoints.GLUE_RECORD,
            account,
            lambda: {"domain": DomainName(domain).value, "host": HostLabel(host).value},
        )

    async def _read(
        self,
        ctx: Context[Any, Any],
        endpoint: DomainEndpoint,
        domain: str,
        account: str | None,
        *,
        page: tuple[int, int] | None = None,
    ) -> dict[str, Any]:
        return await self._runner.read(
            ctx, endpoint, account, lambda: {"domain": DomainName(domain).value}, page=page
        )
