# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools working on a whole zone: export, replace, import and delete it."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.zone_files.zone_file_service import ZoneFileService
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.exceptions import TooManyRecordsError
from gandi_mcp.operations.livedns.zone_replacement import MAX_REPLACED_RECORDS, ZoneReplacement
from gandi_mcp.operations.operation import Operation
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
    FileParameter,
    LiveDnsDomainParameter,
    OverwriteParameter,
    RecordParameter,
    exported,
)
from gandi_mcp.protocol.tools.livedns.record_write_tools import SNAPSHOT_NOTE


class ZoneTools(ToolModule):
    """Export, replace, import and delete a whole zone."""

    def __init__(
        self, runner: EndpointToolRunner, zone_files: ZoneFileService, accounts: AccountsTools
    ) -> None:
        self._runner = runner
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
        changes = (
            (
                self.livedns_zone_replace,
                livedns_endpoints.ZONE_REPLACE,
                "Replace a whole zone",
                "Replace all the records of a zone with the records given (1000 at most; "
                "import a zone file beyond). The NS records at @ are kept unless "
                "remove_apex_ns is set.",
            ),
            (
                self.livedns_zone_import,
                livedns_endpoints.ZONE_IMPORT,
                "Import a zone file",
                "Replace all the records of a zone with a zone file (RFC 1035) of the "
                "gandi-mcp work directory; its content is sent to Gandi, never shown here.",
            ),
            (
                self.livedns_zone_delete,
                livedns_endpoints.ZONE_DELETE,
                "Delete all the records of a zone",
                "Delete every record of a zone; the domain then stops resolving.",
            ),
        )
        for change, change_endpoint, change_title, change_description in changes:
            add_write_tool(
                server, change, change_endpoint, change_title, change_description + SNAPSHOT_NOTE
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

    async def livedns_zone_replace(
        self,
        domain: LiveDnsDomainParameter,
        records: Annotated[
            list[RecordParameter],
            Field(description="All the records of the zone after the change.", min_length=1),
        ],
        ctx: Context[Any, Any],
        *,
        remove_apex_ns: Annotated[
            bool,
            Field(
                description="Also remove the NS records at @ when the records given have "
                "none. Only when the user asks for it."
            ),
        ] = False,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace a whole zone."""

        async def operation() -> Operation:
            if len(records) > MAX_REPLACED_RECORDS:
                raise TooManyRecordsError(f"at most {MAX_REPLACED_RECORDS} records")
            items: list[JsonValue] = [record.record().to_json() for record in records]
            endpoint = (
                livedns_endpoints.ZONE_REPLACE_WITHOUT_APEX_NS
                if remove_apex_ns
                else livedns_endpoints.ZONE_REPLACE
            )
            return ZoneReplacement(
                endpoint,
                DomainName(domain),
                body={"items": items, "remove_apex_ns": remove_apex_ns},
                new_count=len(items),
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_zone_import(
        self,
        domain: LiveDnsDomainParameter,
        file: Annotated[
            str,
            Field(
                description="Zone file to import, relative to the gandi-mcp work directory.",
                min_length=1,
                max_length=255,
            ),
        ],
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Import a zone file."""

        async def operation() -> Operation:
            zone_file = await self._zone_files.read(file)
            return ZoneReplacement(
                livedns_endpoints.ZONE_IMPORT,
                DomainName(domain),
                text_body=zone_file.text,
                new_count=zone_file.record_count,
                params={"file": zone_file.relative_path},
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_zone_delete(
        self,
        domain: LiveDnsDomainParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete all the records of a zone."""

        async def operation() -> Operation:
            return ZoneReplacement(livedns_endpoints.ZONE_DELETE, DomainName(domain))

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)
