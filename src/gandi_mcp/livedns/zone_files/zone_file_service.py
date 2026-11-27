# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export a zone, or one of its snapshots, as a zone file of the work directory."""

from dataclasses import dataclass

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.files.written_file import WrittenFile
from gandi_mcp.livedns.identifiers import SnapshotId
from gandi_mcp.livedns.zone_files.zone_file_summary import record_count
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.livedns import livedns_endpoints
from gandi_mcp.operations.text_file_exporter import TextFileExporter


@dataclass(frozen=True)
class ZoneFileExport:
    """A written zone file and its number of records; the content stays in the file."""

    file: WrittenFile
    record_count: int


class ZoneFileService:
    """Export zone files (the import comes with the zone replacement, sub-batch 1c-2)."""

    def __init__(self, exporter: TextFileExporter) -> None:
        self._exporter = exporter

    async def export(
        self,
        account: AccountName | None,
        context: ConfirmationContext,
        domain: DomainName,
        relative_path: str,
        *,
        overwrite: bool = False,
        snapshot: SnapshotId | None = None,
    ) -> ZoneFileExport:
        """Write the zone of ``domain`` (or its ``snapshot``) to ``relative_path``.

        Raises:
            The errors of :meth:`TextFileExporter.export`.
        """
        if snapshot is None:
            operation = EndpointOperation(livedns_endpoints.ZONE_EXPORT, {"domain": domain.value})
        else:
            operation = EndpointOperation(
                livedns_endpoints.SNAPSHOT_EXPORT,
                {"domain": domain.value, "snapshot": snapshot.value},
            )
        written, text = await self._exporter.export(
            operation, account, context, relative_path, overwrite=overwrite
        )
        return ZoneFileExport(written, record_count(text))
