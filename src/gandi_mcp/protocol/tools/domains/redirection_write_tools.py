# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools creating, changing and deleting the web redirections of a domain."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.write_values import MAX_URL_LENGTH, RedirectionUrl
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    DomainParameter,
    DomainToolRunner,
    add_write_tool,
)

HostParameter = Annotated[
    str, Field(description="Redirected host name, e.g. www.example.com.", max_length=253)
]
UrlParameter = Annotated[
    str, Field(description="Target http or https URL.", max_length=MAX_URL_LENGTH)
]
RedirectionType = Literal["http301", "http302", "cloak"]
Protocol = Literal["http", "https", "httpsonly"]
OverrideParameter = Annotated[
    bool, Field(description="Replace an existing DNS record of the host if needed.")
]


class RedirectionWriteTools(ToolModule):
    """Create, update and delete web redirections."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_web_redirection_create,
                domain_endpoints.WEB_REDIRECTION_CREATE,
                "Create a web redirection",
                "Redirect a host of the domain to a URL (permanent http301, temporary "
                "http302, or cloak in a frame). Fails if the host already has a DNS record: "
                "use domain_web_redirection_replace to replace it.",
            ),
            (
                self.domain_web_redirection_replace,
                domain_endpoints.WEB_REDIRECTION_REPLACE,
                "Create a web redirection replacing a DNS record",
                "Redirect a host to a URL, replacing the DNS record the host already has, "
                "which can interrupt the service on that host.",
            ),
            (
                self.domain_web_redirection_update,
                domain_endpoints.WEB_REDIRECTION_UPDATE,
                "Change a web redirection",
                "Change the target, type or protocol of a web redirection.",
            ),
            (
                self.domain_web_redirection_delete,
                domain_endpoints.WEB_REDIRECTION_DELETE,
                "Delete a web redirection",
                "Delete the web redirection of a host.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_web_redirection_create(
        self,
        domain: DomainParameter,
        host: HostParameter,
        url: UrlParameter,
        ctx: Context[Any, Any],
        *,
        type: RedirectionType = "http301",
        protocol: Protocol = "https",
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a web redirection, without replacing any DNS record."""
        return await self._create(
            ctx,
            domain,
            host=host,
            url=url,
            redirection_type=type,
            protocol=protocol,
            account=account,
            replace=False,
            confirmation_id=None,
        )

    async def domain_web_redirection_replace(
        self,
        domain: DomainParameter,
        host: HostParameter,
        url: UrlParameter,
        ctx: Context[Any, Any],
        *,
        type: RedirectionType = "http301",
        protocol: Protocol = "https",
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a web redirection replacing the DNS record of the host, after confirmation."""
        return await self._create(
            ctx,
            domain,
            host=host,
            url=url,
            redirection_type=type,
            protocol=protocol,
            account=account,
            replace=True,
            confirmation_id=confirmation_id,
        )

    async def _create(
        self,
        ctx: Context[Any, Any],
        domain: str,
        *,
        host: str,
        url: str,
        redirection_type: str,
        protocol: str,
        account: str | None,
        replace: bool,
        confirmation_id: str | None,
    ) -> dict[str, Any]:
        def body() -> JsonValue:
            return {
                "host": DomainName(host).value,
                "url": RedirectionUrl(url).value,
                "type": redirection_type,
                "protocol": protocol,
                "override": replace,
            }

        return await self._runner.write(
            ctx,
            domain_endpoints.WEB_REDIRECTION_REPLACE
            if replace
            else domain_endpoints.WEB_REDIRECTION_CREATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            description_params=lambda: {
                "host": DomainName(host).unicode,
                "url": RedirectionUrl(url).value,
            },
            confirmation_id=confirmation_id,
        )

    async def domain_web_redirection_update(
        self,
        domain: DomainParameter,
        host: HostParameter,
        ctx: Context[Any, Any],
        *,
        url: Annotated[
            str | None,
            Field(default=None, description="New target URL.", max_length=MAX_URL_LENGTH),
        ] = None,
        type: RedirectionType | None = None,
        protocol: Protocol | None = None,
        override: bool | None = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Change a web redirection."""

        def body() -> JsonValue:
            fields: dict[str, JsonValue] = {}
            if url is not None:
                fields["url"] = RedirectionUrl(url).value
            if type is not None:
                fields["type"] = type
            if protocol is not None:
                fields["protocol"] = protocol
            if override is not None:
                fields["override"] = override
            return fields

        return await self._runner.write(
            ctx,
            domain_endpoints.WEB_REDIRECTION_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value, "host": DomainName(host).value},
            body=body,
        )

    async def domain_web_redirection_delete(
        self,
        domain: DomainParameter,
        host: HostParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a web redirection."""
        return await self._runner.write(
            ctx,
            domain_endpoints.WEB_REDIRECTION_DELETE,
            account,
            lambda: {"domain": DomainName(domain).value, "host": DomainName(host).value},
            confirmation_id=confirmation_id,
        )
