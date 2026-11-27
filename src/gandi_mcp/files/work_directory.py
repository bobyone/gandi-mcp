# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the directory where the user's files are read and written."""

from abc import ABC, abstractmethod

from gandi_mcp.files.written_file import WrittenFile


class WorkDirectory(ABC):
    """The only place where gandi-mcp reads and writes the user's files (ADR 15).

    Paths are relative to the directory; a path leading out of it, symbolic links
    included, is always refused. Implementations are blocking: async callers run
    them in a worker thread.
    """

    @abstractmethod
    def check_target(self, relative_path: str, *, overwrite: bool = False) -> str:
        """Check that a file may be written there, before fetching its content.

        Returns:
            The normalized relative path, with ``/`` separators.

        Raises:
            OutsideWorkDirectoryError: if the path leads out of the directory.
            FileExistsInWorkDirectoryError: if the file exists and ``overwrite`` is not set.
        """

    @abstractmethod
    def write(
        self, relative_path: str, content: str, *, overwrite: bool = False, private: bool = False
    ) -> WrittenFile:
        """Write a UTF-8 text file, creating its parent directories.

        Args:
            relative_path: Path relative to the work directory.
            content: Text to write, kept as is (line endings included).
            overwrite: Replace an existing file; otherwise an existing file is refused.
            private: The file holds a secret: only its owner may read it.

        Raises:
            OutsideWorkDirectoryError, FileExistsInWorkDirectoryError,
            WorkDirectoryError: if the file cannot be written.
        """

    @abstractmethod
    def read(self, relative_path: str, max_bytes: int) -> str:
        """Read a UTF-8 text file of at most ``max_bytes`` bytes.

        Raises:
            OutsideWorkDirectoryError, WorkFileNotFoundError, FileTooLargeError,
            UnreadableWorkFileError, WorkDirectoryError: if the file cannot be read.
        """
