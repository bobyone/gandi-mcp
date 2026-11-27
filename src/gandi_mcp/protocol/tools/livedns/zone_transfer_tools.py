# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools reading the zone transfer settings: secondary servers and TSIG keys."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.domains.domain_name import DomainName
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
    EndpointToolRunner,
    add_read_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    OverwriteParameter,
    SharingIdParameter,
    exported,
    sharing_id,
)

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
            return TsigConfiguration(
                TsigKeyId(key_id), TsigSoftware.parse(software), sharing_id(organization_id)
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
