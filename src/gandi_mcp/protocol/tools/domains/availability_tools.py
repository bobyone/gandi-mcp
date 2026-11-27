# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools checking availability and prices, and describing the extensions."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName, TldName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_parameters import DomainParameter
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    PageParameter,
    PerPageParameter,
    add_read_tool,
)

Process = Literal["create", "renew", "transfer", "restore"]
Currency = Literal["EUR", "USD", "GBP", "TWD", "CNY"]
# Gandi: the availability status is only relevant when "create" is priced.
STATUS_NOT_CHECKED = "not checked: availability is only given when create is priced"


def _keeps_status(product: dict[str, JsonValue], only_create: bool) -> bool:
    process = product.get("process")
    return process == "create" if process is not None else only_create


def keep_create_status(data: JsonValue, processes: list[str]) -> JsonValue:
    """Drop the product statuses Gandi says to ignore, and say why.

    Each product has its own ``process``: only the status of ``create`` products is
    kept. A product without ``process`` keeps it only when only create was priced.
    """
    products = data.get("products") if isinstance(data, dict) else None
    if not isinstance(data, dict) or not isinstance(products, list):
        return data
    only_create = set(processes) == {"create"}
    shown: list[JsonValue] = []
    dropped = False
    for product in products:
        if (
            isinstance(product, dict)
            and "status" in product
            and not _keeps_status(product, only_create)
        ):
            without = {key: value for key, value in product.items() if key != "status"}
            without["availability"] = STATUS_NOT_CHECKED
            shown.append(without)
            dropped = True
        else:
            shown.append(product)
    return {**data, "products": shown} if dropped else data


class AvailabilityTools(ToolModule):
    """Availability, quotes and extensions (TLD)."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_read_tool(
            server,
            self.domain_check_availability,
            domain_endpoints.CHECK_AVAILABILITY,
            "Check the availability and prices of a domain",
            "Check whether a domain can be registered (process create), and price its "
            "registration, renewal, transfer or restore per duration, taxes included and "
            "excluded. The availability status only applies to create: for the other "
            "processes it is a price lookup only.",
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
            "Describe an extension (TLD): its category and rules (transfer lock, "
            "authorization code, owner change, reserved to corporate customers).",
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
            adapt=lambda data: keep_create_status(data, list(processes)),
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
