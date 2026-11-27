# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools changing the nameservers, LiveDNS, DNSSEC and glue records of a domain."""

from collections.abc import Callable
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import BaseModel, Field

from gandi_mcp.domains.domain_name import DomainName, HostLabel
from gandi_mcp.domains.write_values import (
    MAX_PUBLIC_KEY_LENGTH,
    DnssecKeyId,
    DnssecKeySpec,
    DnssecKeyType,
    IpAddress,
)
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_parameters import DomainParameter
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    EndpointToolRunner,
    add_write_tool,
)

MAX_NAMESERVERS = 13
MAX_IPS = 13
MAX_KEYS = 10
HostParameter = Annotated[
    str, Field(description="Host name under the domain, e.g. ns1.", max_length=253)
]
IpsParameter = Annotated[
    list[Annotated[str, Field(max_length=45)]],
    Field(description="IPv4 and IPv6 addresses.", min_length=1, max_length=MAX_IPS),
]


class DnssecKeyParameter(BaseModel):
    """A DNSSEC key to publish."""

    algorithm: int = Field(description="Algorithm number, e.g. 13.", ge=0, le=255)
    type: Literal["none", "zsk", "ksk"] = Field(description="Key type.")
    public_key: str = Field(
        description="Public key, in base64.", min_length=1, max_length=MAX_PUBLIC_KEY_LENGTH
    )

    def to_json(self) -> JsonValue:
        """Validate the key and return it as Gandi expects it.

        Raises:
            InvalidDomainInputError: if the key is not valid.
        """
        spec = DnssecKeySpec(self.algorithm, DnssecKeyType(self.type), self.public_key)
        return dict(spec.to_json())


def _ips(values: list[str]) -> list[JsonValue]:
    return [IpAddress(value).value for value in values]


class NameserverWriteTools(ToolModule):
    """Nameservers, LiveDNS, DNSSEC and its keys, glue records."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_nameservers_update,
                domain_endpoints.NAMESERVERS_UPDATE,
                "Replace the nameservers of a domain",
                "Delegate a domain to other nameservers; a wrong list makes it unreachable.",
            ),
            (
                self.domain_livedns_enable,
                domain_endpoints.LIVEDNS_ENABLE,
                "Use the Gandi LiveDNS nameservers",
                "Delegate a domain to the Gandi LiveDNS nameservers, replacing the current ones.",
            ),
            (
                self.domain_dnssec_enable,
                domain_endpoints.DNSSEC_ENABLE,
                "Enable DNSSEC",
                "Enable DNSSEC for a domain using the LiveDNS nameservers.",
            ),
            (
                self.domain_dnssec_disable,
                domain_endpoints.DNSSEC_DISABLE,
                "Disable DNSSEC",
                "Disable DNSSEC for a domain using the LiveDNS nameservers.",
            ),
            (
                self.domain_dnssec_key_add,
                domain_endpoints.DNSSEC_KEY_ADD,
                "Publish a DNSSEC key",
                "Publish a DNSSEC key at the registry, for a domain using other nameservers.",
            ),
            (
                self.domain_dnssec_keys_replace,
                domain_endpoints.DNSSEC_KEYS_REPLACE,
                "Replace the DNSSEC keys",
                "Replace all the DNSSEC keys published at the registry for a domain.",
            ),
            (
                self.domain_dnssec_key_delete,
                domain_endpoints.DNSSEC_KEY_DELETE,
                "Delete a DNSSEC key",
                "Delete one DNSSEC key published at the registry (see domain_dnssec_keys).",
            ),
            (
                self.domain_glue_record_create,
                domain_endpoints.GLUE_RECORD_CREATE,
                "Create a glue record",
                "Create a glue record: a nameserver named under the domain, with its IP addresses.",
            ),
            (
                self.domain_glue_record_update,
                domain_endpoints.GLUE_RECORD_UPDATE,
                "Change the IP addresses of a glue record",
                "Replace the IP addresses of a glue record.",
            ),
            (
                self.domain_glue_record_delete,
                domain_endpoints.GLUE_RECORD_DELETE,
                "Delete a glue record",
                "Delete a glue record of a domain.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_nameservers_update(
        self,
        domain: DomainParameter,
        nameservers: Annotated[
            list[Annotated[str, Field(max_length=253)]],
            Field(description="Nameserver names.", min_length=1, max_length=MAX_NAMESERVERS),
        ],
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace the nameservers."""
        return await self._write(
            ctx,
            domain_endpoints.NAMESERVERS_UPDATE,
            domain,
            account,
            lambda: {"nameservers": [DomainName(name).value for name in nameservers]},
            confirmation_id=confirmation_id,
        )

    async def domain_livedns_enable(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Use LiveDNS."""
        return await self._write(
            ctx, domain_endpoints.LIVEDNS_ENABLE, domain, account, confirmation_id=confirmation_id
        )

    async def domain_dnssec_enable(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Enable DNSSEC."""
        return await self._write(ctx, domain_endpoints.DNSSEC_ENABLE, domain, account)

    async def domain_dnssec_disable(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Disable DNSSEC."""
        return await self._write(
            ctx, domain_endpoints.DNSSEC_DISABLE, domain, account, confirmation_id=confirmation_id
        )

    async def domain_dnssec_key_add(
        self,
        domain: DomainParameter,
        key: DnssecKeyParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Publish a DNSSEC key."""
        return await self._write(ctx, domain_endpoints.DNSSEC_KEY_ADD, domain, account, key.to_json)

    async def domain_dnssec_keys_replace(
        self,
        domain: DomainParameter,
        keys: Annotated[
            list[DnssecKeyParameter], Field(description="Keys.", min_length=1, max_length=MAX_KEYS)
        ],
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace the DNSSEC keys."""
        return await self._write(
            ctx,
            domain_endpoints.DNSSEC_KEYS_REPLACE,
            domain,
            account,
            lambda: {"keys": [key.to_json() for key in keys]},
            confirmation_id=confirmation_id,
        )

    async def domain_dnssec_key_delete(
        self,
        domain: DomainParameter,
        key_id: Annotated[str, Field(description="Key identifier.", max_length=64)],
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a DNSSEC key."""
        return await self._runner.write(
            ctx,
            domain_endpoints.DNSSEC_KEY_DELETE,
            account,
            lambda: {"domain": DomainName(domain).value, "id": DnssecKeyId(key_id).value},
            confirmation_id=confirmation_id,
        )

    async def domain_glue_record_create(
        self,
        domain: DomainParameter,
        host: HostParameter,
        ips: IpsParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a glue record."""
        return await self._write(
            ctx,
            domain_endpoints.GLUE_RECORD_CREATE,
            domain,
            account,
            lambda: {"name": HostLabel(host).value, "ips": _ips(ips)},
        )

    async def domain_glue_record_update(
        self,
        domain: DomainParameter,
        host: HostParameter,
        ips: IpsParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace the IP addresses of a glue record."""
        return await self._runner.write(
            ctx,
            domain_endpoints.GLUE_RECORD_UPDATE,
            account,
            lambda: {"domain": DomainName(domain).value, "host": HostLabel(host).value},
            body=lambda: {"ips": _ips(ips)},
        )

    async def domain_glue_record_delete(
        self,
        domain: DomainParameter,
        host: HostParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a glue record."""
        return await self._runner.write(
            ctx,
            domain_endpoints.GLUE_RECORD_DELETE,
            account,
            lambda: {"domain": DomainName(domain).value, "host": HostLabel(host).value},
            confirmation_id=confirmation_id,
        )

    async def _write(
        self,
        ctx: Context[Any, Any],
        endpoint: Endpoint,
        domain: str,
        account: str | None,
        body: Callable[[], JsonValue] | None = None,
        *,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._runner.write(
            ctx,
            endpoint,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )
