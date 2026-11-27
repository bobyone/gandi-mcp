# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the signing keys of a zone (LiveDNS DNSSEC)."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.livedns.identifiers import SigningKeyId
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    add_read_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import LiveDnsDomainParameter


class SigningKeyTools(ToolModule):
    """Signing keys of a zone, distinct from the DNSSEC keys published at the registry."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.livedns_signing_keys,
                livedns_endpoints.SIGNING_KEYS,
                "List the signing keys of a zone",
                "List the keys LiveDNS signs a zone with (KSK 257, ZSK 256); the keys "
                "published at the registry are given by domain_dnssec_keys.",
            ),
            (
                self.livedns_signing_key,
                livedns_endpoints.SIGNING_KEY,
                "Show a signing key",
                "Show a signing key of a zone: algorithm, flags, DS and public key.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_read_tool(server, function, endpoint, title, description)

    async def livedns_signing_keys(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the signing keys of a zone."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.SIGNING_KEYS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )

    async def livedns_signing_key(
        self,
        domain: LiveDnsDomainParameter,
        key_id: Annotated[
            str,
            Field(description="Signing key identifier, from livedns_signing_keys.", max_length=64),
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Show a signing key."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.SIGNING_KEY,
            account,
            lambda: {"domain": DomainName(domain).value, "key": SigningKeyId(key_id).value},
        )
