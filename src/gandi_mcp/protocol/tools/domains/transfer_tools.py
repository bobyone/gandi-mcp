# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools following owner changes and transfers in."""

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_parameters import DomainParameter
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    add_read_tool,
)


class TransferTools(ToolModule):
    """Owner change and transfer in follow-up, transfer in check."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_owner_change_status,
                domain_endpoints.OWNER_CHANGE_STATUS,
                "Follow the owner change of a domain",
                "Show the progress of an owner change, including the steps left to the contacts.",
            ),
            (
                self.domain_transfer_in_status,
                domain_endpoints.TRANSFER_IN_STATUS,
                "Follow the transfer in of a domain",
                "Show the progress of a domain transfer to Gandi.",
            ),
            (
                self.domain_transfer_in_check,
                domain_endpoints.TRANSFER_IN_CHECK,
                "Check whether a domain can be transferred in",
                "Check whether a domain can be transferred to Gandi, and why not. Changes nothing.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_read_tool(server, function, endpoint, title, description)

    async def domain_owner_change_status(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Follow the owner change of a domain."""
        return await self._read(ctx, domain_endpoints.OWNER_CHANGE_STATUS, domain, account)

    async def domain_transfer_in_status(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Follow the transfer in of a domain."""
        return await self._read(ctx, domain_endpoints.TRANSFER_IN_STATUS, domain, account)

    async def domain_transfer_in_check(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Check whether a domain can be transferred in."""
        # The authorization code is optional for this check; it is not sent through the
        # model (see the transfer in design).
        return await self._runner.read(
            ctx,
            domain_endpoints.TRANSFER_IN_CHECK,
            account,
            lambda: {"domain": DomainName(domain).value},
            body={},
        )

    async def _read(
        self, ctx: Context[Any, Any], endpoint: Endpoint, domain: str, account: str | None
    ) -> dict[str, Any]:
        return await self._runner.read(
            ctx, endpoint, account, lambda: {"domain": DomainName(domain).value}
        )
