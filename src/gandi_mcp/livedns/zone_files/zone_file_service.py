# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Export a zone or a snapshot as a zone file of the work directory, and read one."""

import asyncio
from dataclasses import dataclass

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.files.work_directory import WorkDirectory
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


@dataclass(frozen=True)
class ZoneFile:
    """A zone file read from the work directory, never shown to the model.

    Attributes:
        relative_path: Its path relative to the work directory.
        text: Its content, sent to Gandi only.
        record_count: Its number of records (name and type pairs, SOA excluded).
    """

    relative_path: str
    text: str
    record_count: int


class ZoneFileService:
    """Export zone files, and read the zone file of an import (sent by the zone
    replacement)."""

    def __init__(
        self, exporter: TextFileExporter, work_directory: WorkDirectory, max_zone_file_size: int
    ) -> None:
        """``max_zone_file_size`` is the largest zone file read, in bytes
        (``files.max_zone_file_size``)."""
        self._exporter = exporter
        self._work_directory = work_directory
        self._max_size = max_zone_file_size

    async def read(self, relative_path: str) -> ZoneFile:
        """Read a zone file of the work directory, bounded in size.

        Raises:
            WorkDirectoryError: if it is outside the directory, missing, too large or
                not UTF-8 text.
        """
        text = await asyncio.to_thread(self._work_directory.read, relative_path, self._max_size)
        return ZoneFile(relative_path, text, record_count(text))

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
