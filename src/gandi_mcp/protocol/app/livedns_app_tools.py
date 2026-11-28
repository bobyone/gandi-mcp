# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""MCP App tool of the "DNS zone" screen: the records with their full values (ADR 16)."""

from typing import Annotated, Any

from mcp.server.apps import Apps, client_supports_apps
from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.app.accounts_app_tools import APP_ONLY
from gandi_mcp.protocol.app.app_resource import APP_URI
from gandi_mcp.protocol.app_module import AppModule
from gandi_mcp.protocol.error_presenter import AppOnlyToolError
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    PageParameter,
    PerPageParameter,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import LiveDnsDomainParameter
from gandi_mcp.protocol.tools.livedns.record_read_tools import RecordSort


class LiveDnsAppTools(AppModule):
    """``app_livedns_records``: the only LiveDNS tool reserved to the App.

    Its runner presents results without the long text filter: a DKIM key or a long
    TXT value reaches the App in full, and a result of a call made by the App never
    reaches the model (ADR 12). It is refused unless the client negotiated the MCP
    Apps extension, so that a client that does not render the App cannot hand those
    values to its model. Every other operation of the screen calls the model tools.
    """

    def __init__(self, runner: EndpointToolRunner, accounts: AccountsTools) -> None:
        """``runner`` must present results without the long text filter."""
        self._runner = runner
        self._accounts = accounts

    def register(self, apps: Apps) -> None:
        apps.tool(
            resource_uri=APP_URI,
            visibility=APP_ONLY,
            name="app_livedns_records",
            description="List the records of a zone with their full values. Only for the "
            "Gandi app.",
            annotations=ToolAnnotations(
                read_only_hint=True, idempotent_hint=True, open_world_hint=True
            ),
        )(self.app_livedns_records)

    async def app_livedns_records(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        *,
        record_type: Annotated[
            str | None,
            Field(default=None, description="Only the records of this type.", max_length=10),
        ] = None,
        sort_by: Annotated[
            RecordSort, Field(description="Sort order; a leading - reverses it.")
        ] = "rrset_name",
        page: PageParameter = 1,
        per_page: PerPageParameter = 25,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """List the records of a zone for the App, values in full."""
        if not client_supports_apps(ctx):

            async def refused() -> dict[str, Any]:
                raise AppOnlyToolError

            return await self._accounts.guard(refused)
        return await self._runner.read(
            ctx,
            livedns_endpoints.RECORD_LIST,
            account,
            lambda: {"domain": DomainName(domain).value},
            query=lambda: {
                "rrset_type": RecordType.parse(record_type).value if record_type else None,
                "sort_by": sort_by,
            },
            page=(page, per_page),
        )
