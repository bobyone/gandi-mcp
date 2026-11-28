# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools changing the records of a zone: create, add or remove values, replace,
delete."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.record import Record, record_values
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.ttl import Ttl
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.livedns.name_records_change import NameRecordsChange
from gandi_mcp.operations.livedns.record_change import RecordChange
from gandi_mcp.operations.operation import Operation
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    EndpointToolRunner,
    add_write_tool,
)
from gandi_mcp.protocol.tools.livedns.livedns_parameters import (
    LiveDnsDomainParameter,
    RecordNameParameter,
    RecordTypeParameter,
    RecordValuesParameter,
    TtlParameter,
    TypedRecordParameter,
)

SNAPSHOT_NOTE = (
    " The user is shown the counted effect and chooses, outside the conversation, "
    "whether a snapshot is taken first."
)


class RecordWriteTools(ToolModule):
    """Create a record, add or remove values, replace or delete a record or the records
    of a name; the destructive changes are confirmed with their counted effect."""

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
        changes = (
            (
                self.livedns_record_replace,
                livedns_endpoints.RECORD_REPLACE,
                "Replace a DNS record",
                "Replace all the values of the record of a name and type.",
            ),
            (
                self.livedns_record_values_remove,
                livedns_endpoints.RECORD_VALUES_REMOVE,
                "Remove values from a DNS record",
                "Remove some values of the record of a name and type; without values left, "
                "the record is deleted.",
            ),
            (
                self.livedns_record_delete,
                livedns_endpoints.RECORD_DELETE,
                "Delete a DNS record",
                "Delete the record of a name and type.",
            ),
            (
                self.livedns_name_records_replace,
                livedns_endpoints.NAME_RECORDS_REPLACE,
                "Replace the DNS records of a name",
                "Replace all the records of a name, every type, with the records given.",
            ),
            (
                self.livedns_name_records_delete,
                livedns_endpoints.NAME_RECORDS_DELETE,
                "Delete the DNS records of a name",
                "Delete all the records of a name, every type.",
            ),
        )
        for change, change_endpoint, change_title, change_description in changes:
            add_write_tool(
                server, change, change_endpoint, change_title, change_description + SNAPSHOT_NOTE
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

    async def livedns_record_replace(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: RecordTypeParameter,
        values: RecordValuesParameter,
        ctx: Context[Any, Any],
        *,
        ttl: TtlParameter = None,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace a DNS record."""

        async def operation() -> Operation:
            record = Record.of(name, record_type, values, ttl)
            return RecordChange(
                livedns_endpoints.RECORD_REPLACE,
                DomainName(domain),
                record.name,
                record.type,
                body=record.values_json(),
                new_values=record.values,
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_record_values_remove(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: RecordTypeParameter,
        values: RecordValuesParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Remove values from a DNS record."""

        async def operation() -> Operation:
            kind = RecordType.parse(record_type)
            removed = record_values(kind, values)
            return RecordChange(
                livedns_endpoints.RECORD_VALUES_REMOVE,
                DomainName(domain),
                RecordName(name),
                kind,
                body={"remove_rrset_values": [value.value for value in removed]},
                removed_values=removed,
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_record_delete(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        record_type: RecordTypeParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a DNS record."""

        async def operation() -> Operation:
            return RecordChange(
                livedns_endpoints.RECORD_DELETE,
                DomainName(domain),
                RecordName(name),
                RecordType.parse(record_type),
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_name_records_replace(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        records: Annotated[
            list[TypedRecordParameter],
            Field(
                description="The records of the name after the change.", min_length=1, max_length=50
            ),
        ],
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Replace the DNS records of a name."""

        async def operation() -> Operation:
            built = [record.record(name) for record in records]
            items: list[JsonValue] = [
                {"rrset_type": record.type.value, **record.values_json()} for record in built
            ]
            return NameRecordsChange(
                livedns_endpoints.NAME_RECORDS_REPLACE,
                DomainName(domain),
                RecordName(name),
                body={"items": items},
                new_count=len(built),
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)

    async def livedns_name_records_delete(
        self,
        domain: LiveDnsDomainParameter,
        name: RecordNameParameter,
        ctx: Context[Any, Any],
        *,
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete the DNS records of a name."""

        async def operation() -> Operation:
            return NameRecordsChange(
                livedns_endpoints.NAME_RECORDS_DELETE, DomainName(domain), RecordName(name)
            )

        return await self._runner.write_operation(ctx, operation, account, confirmation_id)
