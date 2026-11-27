# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools on the zone transfer settings: secondary servers and TSIG keys."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.write_values import IpAddress
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.identifiers import TsigKeyId
from gandi_mcp.livedns.tsig_software import TsigSoftware
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.tsig_configuration import CONFIGURATION, TsigConfiguration
from gandi_mcp.operations.text_file_exporter import TextFileExporter
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    EndpointToolRunner,
    add_read_tool,
    add_write_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    OverwriteParameter,
    SharingIdParameter,
    exported,
    sharing_id,
)

IpParameter = Annotated[
    str, Field(description="IPv4 or IPv6 address of the secondary server.", max_length=45)
]
TsigKeyIdParameter = Annotated[
    str, Field(description="TSIG key identifier, from livedns_tsig_keys.", max_length=64)
]
KEY_NOTE = " The secret of a key is never returned: it is shown as hidden."


def configuration(data: JsonValue) -> str | None:
    """The full configuration sample, secret included, for a file."""
    value = data.get(CONFIGURATION) if isinstance(data, dict) else None
    return value if isinstance(value, str) else None


class ZoneTransferTools(ToolModule):
    """Secondary servers of a zone, TSIG keys of the account and of a zone."""

    def __init__(
        self, runner: EndpointToolRunner, exporter: TextFileExporter, accounts: AccountsTools
    ) -> None:
        self._runner = runner
        self._exporter = exporter
        self._accounts = accounts

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.livedns_secondary_servers,
                livedns_endpoints.SECONDARY_SERVERS,
                "List the secondary servers of a zone",
                "List the IP addresses of the secondary servers allowed to transfer a zone.",
            ),
            (
                self.livedns_tsig_keys,
                livedns_endpoints.TSIG_KEYS,
                "List the TSIG keys",
                "List the TSIG keys of the account, used to authenticate zone transfers."
                + KEY_NOTE,
            ),
            (
                self.livedns_tsig_key,
                livedns_endpoints.TSIG_KEY_DETAILS,
                "Show a TSIG key",
                "Show a TSIG key of the account." + KEY_NOTE,
            ),
            (
                self.livedns_tsig_config,
                livedns_endpoints.TSIG_CONFIG,
                "Show the configuration sample of a TSIG key",
                "Give the configuration of a secondary server software (bind, knot, nsd, "
                "powerdns) for a TSIG key, with its secret hidden. With file, the full "
                "sample, secret included, is written to the gandi-mcp work directory instead "
                "(owner-only file) and only the file name is returned.",
            ),
            (
                self.livedns_domain_tsig_keys,
                livedns_endpoints.DOMAIN_TSIG_KEYS,
                "List the TSIG keys of a zone",
                "List the TSIG keys associated with the zone of a domain.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_read_tool(server, function, endpoint, title, description)
        writes = (
            (
                self.livedns_secondary_server_add,
                livedns_endpoints.SECONDARY_SERVER_ADD,
                "Allow a secondary server",
                "Allow the secondary server at an IP address to transfer a zone.",
            ),
            (
                self.livedns_secondary_server_remove,
                livedns_endpoints.SECONDARY_SERVER_REMOVE,
                "Remove a secondary server",
                "Stop allowing the secondary server at an IP address to transfer a zone.",
            ),
            (
                self.livedns_tsig_key_create,
                livedns_endpoints.TSIG_KEY_CREATE,
                "Create a TSIG key",
                "Create a TSIG key in the account; its secret is never returned (use "
                "livedns_tsig_config with a file for the server configuration).",
            ),
            (
                self.livedns_domain_tsig_key_add,
                livedns_endpoints.DOMAIN_TSIG_KEY_ADD,
                "Associate a TSIG key with a zone",
                "Let the TSIG key authenticate the transfers of the zone of a domain.",
            ),
            (
                self.livedns_domain_tsig_key_remove,
                livedns_endpoints.DOMAIN_TSIG_KEY_REMOVE,
                "Dissociate a TSIG key from a zone",
                "Stop using the TSIG key for the transfers of the zone of a domain.",
            ),
        )
        for write, write_endpoint, write_title, write_description in writes:
            add_write_tool(server, write, write_endpoint, write_title, write_description)

    async def livedns_secondary_servers(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the secondary servers of a zone."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.SECONDARY_SERVERS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )

    async def livedns_tsig_keys(
        self,
        ctx: Context[Any, Any],
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the TSIG keys."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.TSIG_KEYS,
            account,
            query=lambda: {"sharing_id": sharing_id(organization_id)},
        )

    async def livedns_tsig_key(
        self,
        key_id: TsigKeyIdParameter,
        ctx: Context[Any, Any],
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Show a TSIG key."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.TSIG_KEY_DETAILS,
            account,
            lambda: {"key": TsigKeyId(key_id).value},
            query=lambda: {"sharing_id": sharing_id(organization_id)},
        )

    async def livedns_tsig_config(
        self,
        key_id: TsigKeyIdParameter,
        software: Annotated[
            str, Field(description="Server software: bind, knot, nsd or powerdns.", max_length=10)
        ],
        ctx: Context[Any, Any],
        *,
        file: Annotated[
            str | None,
            Field(
                default=None,
                description="File to write the full sample to, relative to the gandi-mcp "
                "work directory. Only when the user asks for a file.",
                min_length=1,
                max_length=255,
            ),
        ] = None,
        overwrite: OverwriteParameter = False,
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Show the configuration sample of a TSIG key."""

        def operation() -> TsigConfiguration:
            # Shown to the model without a file: fail closed if the secret cannot be hidden.
            return TsigConfiguration(
                TsigKeyId(key_id),
                TsigSoftware.parse(software),
                sharing_id(organization_id),
                secret_required=file is None,
            )

        if file is None:
            return await self._runner.read_operation(ctx, operation, account)

        async def run() -> dict[str, Any]:
            written, _ = await self._exporter.export(
                operation(),
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                file,
                overwrite=overwrite,
                extract=configuration,
                private=True,
            )
            return exported(written)

        return await self._accounts.guard(run)

    async def livedns_domain_tsig_keys(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the TSIG keys of a zone."""
        return await self._runner.read(
            ctx,
            livedns_endpoints.DOMAIN_TSIG_KEYS,
            account,
            lambda: {"domain": DomainName(domain).value},
        )

    async def livedns_secondary_server_add(
        self,
        domain: LiveDnsDomainParameter,
        ip: IpParameter,
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Allow a secondary server to transfer a zone."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.SECONDARY_SERVER_ADD,
            account,
            lambda: {"domain": DomainName(domain).value, "ip": IpAddress(ip).value},
        )

    async def livedns_secondary_server_remove(
        self,
        domain: LiveDnsDomainParameter,
        ip: IpParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Stop allowing a secondary server to transfer a zone."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.SECONDARY_SERVER_REMOVE,
            account,
            lambda: {"domain": DomainName(domain).value, "ip": IpAddress(ip).value},
            confirmation_id=confirmation_id,
        )

    async def livedns_tsig_key_create(
        self,
        ctx: Context[Any, Any],
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a TSIG key."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.TSIG_KEY_CREATE,
            account,
            dict,
            query=lambda: {"sharing_id": sharing_id(organization_id)},
        )

    async def livedns_domain_tsig_key_add(
        self,
        domain: LiveDnsDomainParameter,
        key_id: TsigKeyIdParameter,
        ctx: Context[Any, Any],
        *,
        organization_id: SharingIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Associate a TSIG key with a zone."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.DOMAIN_TSIG_KEY_ADD,
            account,
            lambda: {"domain": DomainName(domain).value, "key": TsigKeyId(key_id).value},
            query=lambda: {"sharing_id": sharing_id(organization_id)},
        )

    async def livedns_domain_tsig_key_remove(
        self,
        domain: LiveDnsDomainParameter,
        key_id: TsigKeyIdParameter,
        ctx: Context[Any, Any],
        *,
        organization_id: SharingIdParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Dissociate a TSIG key from a zone."""
        return await self._runner.write(
            ctx,
            livedns_endpoints.DOMAIN_TSIG_KEY_REMOVE,
            account,
            lambda: {"domain": DomainName(domain).value, "key": TsigKeyId(key_id).value},
            query=lambda: {"sharing_id": sharing_id(organization_id)},
            confirmation_id=confirmation_id,
        )
