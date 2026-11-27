# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the web redirections of a domain."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
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


class RedirectionTools(ToolModule):
    """Web redirections."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_read_tool(
            server,
            self.domain_web_redirections,
            domain_endpoints.WEB_REDIRECTIONS,
            "List the web redirections of a domain",
            "List the web redirections of a domain, with their target and type.",
        )
        add_read_tool(
            server,
            self.domain_web_redirection,
            domain_endpoints.WEB_REDIRECTION,
            "Describe a web redirection",
            "Describe the web redirection of one host of a domain.",
        )

    async def domain_web_redirections(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the web redirections of a domain."""
        return await self._runner.read(
            ctx,
            domain_endpoints.WEB_REDIRECTIONS,
            account,
            lambda: {"domain": DomainName(domain).value},
            page=(page, per_page),
        )

    async def domain_web_redirection(
        self,
        domain: DomainParameter,
        host: Annotated[
            str,
            Field(description="Redirected host name, e.g. www.example.com.", max_length=253),
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Describe a web redirection."""
        return await self._runner.read(
            ctx,
            domain_endpoints.WEB_REDIRECTION,
            account,
            lambda: {"domain": DomainName(domain).value, "host": DomainName(host).value},
        )
