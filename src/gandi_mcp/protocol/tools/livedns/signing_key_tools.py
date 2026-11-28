# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools on the signing keys of a zone (LiveDNS DNSSEC)."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.livedns.identifiers import SigningKeyId
from gandi_mcp.livedns.signing_key_flag import SigningKeyFlag
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    EndpointToolRunner,
    add_read_tool,
    add_write_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import LiveDnsDomainParameter

SigningKeyIdParameter = Annotated[
    str, Field(description="Signing key identifier, from livedns_signing_keys.", max_length=64)
]


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
        writes = (
            (
                self.livedns_signing_key_create,
                livedns_endpoints.SIGNING_KEY_CREATE,
                "Create a signing key",
                "Have LiveDNS generate a new signing key for a zone. Its DS record must then "
                "be published at the registry (domain_dnssec_keys_replace) for DNSSEC to work.",
            ),
            (
                self.livedns_signing_key_restore,
                livedns_endpoints.SIGNING_KEY_RESTORE,
                "Restore a deleted signing key",
                "Restore a signing key of a zone deleted earlier.",
            ),
            (
                self.livedns_signing_key_delete,
                livedns_endpoints.SIGNING_KEY_DELETE,
                "Delete a signing key",
                "Delete a signing key of a zone; resolution may break if its DS record is "
                "still published at the registry.",
            ),
        )
        for write, write_endpoint, write_title, write_description in writes:
            add_write_tool(server, write, write_endpoint, write_title, write_description)

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
        key_id: SigningKeyIdParameter,
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

    async def livedns_signing_key_create(
        self,
        domain: LiveDnsDomainParameter,
        flags: Annotated[
            Literal[256, 257],
            Field(description="257 for a key signing key (KSK), 256 for a zone signing key (ZSK)."),
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a signing key."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.SIGNING_KEY_CREATE,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=lambda: {"flags": int(SigningKeyFlag.parse(flags))},
        )

    async def livedns_signing_key_restore(
        self,
        domain: LiveDnsDomainParameter,
        key_id: SigningKeyIdParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Restore a deleted signing key."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.SIGNING_KEY_RESTORE,
            account,
            lambda: {"domain": DomainName(domain).value, "key": SigningKeyId(key_id).value},
            body=lambda: {"deleted": False},
        )

    async def livedns_signing_key_delete(
        self,
        domain: LiveDnsDomainParameter,
        key_id: SigningKeyIdParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a signing key."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.SIGNING_KEY_DELETE,
            account,
            lambda: {"domain": DomainName(domain).value, "key": SigningKeyId(key_id).value},
            confirmation_id=confirmation_id,
        )
