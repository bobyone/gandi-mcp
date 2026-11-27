# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Write the text read by an operation to the work directory, out of the model's sight."""

import asyncio
from collections.abc import Callable

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.files.work_directory import WorkDirectory
from gandi_mcp.files.written_file import WrittenFile
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.untrusted_result import UntrustedResult


def whole_text(data: JsonValue) -> str | None:
    """The data itself, when it is a text (zone file)."""
    return data if isinstance(data, str) else None


class TextFileExporter:
    """Run a read operation and write its text to a file of the work directory.

    1. Check that the target stays in the work directory and does not exist (unless
       overwriting is asked), before asking Gandi.
    2. Run the operation with the usual rules (account, token, untrusted data).
    3. Write the text; only the written file is described to the caller.
    """

    def __init__(self, executor: OperationExecutor, work_directory: WorkDirectory) -> None:
        self._executor = executor
        self._work_directory = work_directory

    async def export(
        self,
        operation: Operation,
        account: AccountName | None,
        context: ConfirmationContext,
        relative_path: str,
        *,
        overwrite: bool = False,
        extract: Callable[[JsonValue], str | None] = whole_text,
        private: bool = False,
    ) -> tuple[WrittenFile, str]:
        """Export the text and return the written file and the text itself.

        Args:
            extract: Picks the text in the operation data.
            private: The text holds a secret (owner-only file).

        Raises:
            WorkDirectoryError: if the file cannot be written there.
            GandiUnexpectedResponseError: if Gandi returned no text.
            The errors of :meth:`OperationExecutor.run`.
        """
        if operation.category.is_write:
            raise TypeError(f"{operation.name}: only a read is exported")
        await asyncio.to_thread(
            self._work_directory.check_target, relative_path, overwrite=overwrite
        )
        result = await self._executor.run(operation, account, context)
        if not isinstance(result, UntrustedResult):  # pragma: no cover - reads are never confirmed
            raise TypeError("a read operation cannot wait for a confirmation")
        text = extract(result.data)
        if text is None:
            raise GandiUnexpectedResponseError(f"{operation.name}: no text to export")
        written = await asyncio.to_thread(
            self._work_directory.write,
            relative_path,
            text,
            overwrite=overwrite,
            private=private,
        )
        return written, text
