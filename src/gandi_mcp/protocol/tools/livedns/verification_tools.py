# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tool publishing a domain verification value (ACME DNS-01 challenge...)."""

from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.livedns.record import record_values
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    EndpointToolRunner,
    add_write_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    RecordNameParameter,
    RecordValuesParameter,
)


class VerificationTools(ToolModule):
    """Domain verification values, for example for a certificate (ACME DNS-01)."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_write_tool(
            server,
            self.livedns_domain_verification,
            livedns_endpoints.DOMAIN_VERIFICATION,
            "Publish a domain verification value",
            "Add a TXT or CNAME validation value (for example _acme-challenge for an ACME "
            "DNS-01 challenge), leaving the rest of the zone untouched. The token needs "
            "the domain verification permission.",
        )

    async def livedns_domain_verification(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: Annotated[Literal["TXT", "CNAME"], Field(description="TXT or CNAME.")],
        values: RecordValuesParameter,
        ctx: Context[Any, Any],
        *,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Publish a domain verification value."""
        kind = RecordType(record_type)
        return await self._runner.write(
            ctx,
            livedns_endpoints.DOMAIN_VERIFICATION,
            account,
            lambda: {
                "domain": DomainName(domain).value,
                "name": RecordName(name).value,
                "type": kind.value,
            },
            body=lambda: {"rrset_values": [value.value for value in record_values(kind, values)]},
        )
