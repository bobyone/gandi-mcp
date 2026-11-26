# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools checking availability and prices, and describing the extensions."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName, TldName
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    DomainParameter,
    DomainToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
)

Process = Literal["create", "renew", "transfer", "restore"]
Currency = Literal["EUR", "USD", "GBP", "TWD", "CNY"]


class AvailabilityTools(ToolModule):
    """Availability, quotes and extensions (TLD)."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_read_tool(
            server,
            self.domain_check_availability,
            domain_endpoints.CHECK_AVAILABILITY,
            "Check the availability of a domain",
            "Check whether a domain can be registered, renewed, transferred or restored, "
            "with its prices (quote) per duration, taxes included and excluded.",
        )
        add_read_tool(
            server,
            self.domain_list_tlds,
            domain_endpoints.LIST_TLDS,
            "List the extensions",
            "List the extensions (TLD) sold by Gandi.",
        )
        add_read_tool(
            server,
            self.domain_tld_details,
            domain_endpoints.TLD_DETAILS,
            "Describe an extension",
            "Describe an extension (TLD): its rules, features and allowed durations.",
        )

    async def domain_check_availability(
        self,
        name: DomainParameter,
        ctx: Context[Any, Any],
        processes: Annotated[
            list[Process],
            Field(description="Operations to price.", min_length=1, max_length=4),
        ] = ["create"],  # noqa: B006 - pydantic copies the default
        currency: Annotated[
            Currency | None, Field(default=None, description="Currency of the prices.")
        ] = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Check a domain and price it."""
        return await self._runner.read(
            ctx,
            domain_endpoints.CHECK_AVAILABILITY,
            account,
            query=lambda: {
                "name": DomainName(name).value,
                "processes": sorted(set(processes)),
                "currency": currency,
            },
        )

    async def domain_list_tlds(
        self,
        ctx: Context[Any, Any],
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the extensions."""
        return await self._runner.read(
            ctx, domain_endpoints.LIST_TLDS, account, page=(page, per_page)
        )

    async def domain_tld_details(
        self,
        tld: Annotated[str, Field(description="Extension, e.g. fr or com.", max_length=63)],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Describe an extension."""
        return await self._runner.read(
            ctx, domain_endpoints.TLD_DETAILS, account, lambda: {"tld": TldName(tld).value}
        )
