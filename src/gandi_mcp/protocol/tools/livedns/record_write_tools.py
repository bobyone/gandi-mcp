# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools adding records and record values to a zone."""

from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.record import Record, record_values
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.ttl import Ttl
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
    RecordTypeParameter,
    RecordValuesParameter,
    TtlParameter,
)


class RecordWriteTools(ToolModule):
    """Create a record, add values to a record (the destructive changes come with the
    zone changes)."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        add_write_tool(
            server,
            self.livedns_record_create,
            livedns_endpoints.RECORD_CREATE,
            "Create a DNS record",
            "Create the record of a name and type. If it exists with the same values, "
            "nothing changes (status unchanged); with other values, Gandi refuses: add "
            "values with livedns_record_values_add or replace it with livedns_record_replace.",
        )
        add_write_tool(
            server,
            self.livedns_record_values_add,
            livedns_endpoints.RECORD_VALUES_ADD,
            "Add values to a DNS record",
            "Add values to the record of a name and type, keeping its other values; the "
            "record is created if needed.",
        )

    async def livedns_record_create(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: RecordTypeParameter,
        values: RecordValuesParameter,
        ctx: Context[Any, Any],
        *,
        ttl: TtlParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Create a DNS record."""

        def record() -> Record:
            return Record.of(name, record_type, values, ttl)

        return await self._runner.write(
            ctx,
            livedns_endpoints.RECORD_CREATE,
            account,
            lambda: {
                "domain": DomainName(domain).value,
                "name": record().name.value,
                "type": record().type.value,
            },
            body=lambda: record().values_json(),
        )

    async def livedns_record_values_add(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: RecordTypeParameter,
        values: RecordValuesParameter,
        ctx: Context[Any, Any],
        *,
        ttl: TtlParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Add values to a DNS record."""

        def body() -> JsonValue:
            kind = RecordType.parse(record_type)
            fields: dict[str, JsonValue] = {
                "add_rrset_values": [value.value for value in record_values(kind, values)]
            }
            if ttl is not None:
                fields["rrset_ttl"] = Ttl(ttl).seconds
            return fields

        return await self._runner.write(
            ctx,
            livedns_endpoints.RECORD_VALUES_ADD,
            account,
            lambda: {
                "domain": DomainName(domain).value,
                "name": RecordName(name).value,
                "type": RecordType.parse(record_type).value,
            },
            body=body,
        )
