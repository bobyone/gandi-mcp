# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools working on a whole zone: its export as a zone file."""

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.livedns.zone_files.zone_file_service import ZoneFileService
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.endpoint_tool_runner import AccountParameter, add_read_tool
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    FileParameter,
    LiveDnsDomainParameter,
    OverwriteParameter,
    exported,
)


class ZoneTools(ToolModule):
    """Export a zone (its replacement and import come in sub-batch 1c-2)."""

    def __init__(self, zone_files: ZoneFileService, accounts: AccountsTools) -> None:
        self._zone_files = zone_files
        self._accounts = accounts

    def register(self, server: MCPServer) -> None:
        add_read_tool(
            server,
            self.livedns_zone_export,
            livedns_endpoints.ZONE_EXPORT,
            "Export a zone to a file",
            "Write the zone of a domain as a zone file (RFC 1035) in the gandi-mcp work "
            "directory; only the file name, its size and its number of records are returned.",
        )

    async def livedns_zone_export(
        self,
        domain: LiveDnsDomainParameter,
        file: FileParameter,
        ctx: Context[Any, Any],
        *,
        overwrite: OverwriteParameter = False,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Export a zone to a file."""

        async def run() -> dict[str, Any]:
            export = await self._zone_files.export(
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                DomainName(domain),
                file,
                overwrite=overwrite,
            )
            return exported(export.file, record_count=export.record_count)

        return await self._accounts.guard(run)
