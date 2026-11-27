# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Work directory keeping its files in memory, with the same refusals as the real one."""

from dataclasses import dataclass, field

from gandi_mcp.files.exceptions import (
    FileExistsInWorkDirectoryError,
    FileTooLargeError,
    OutsideWorkDirectoryError,
    WorkFileNotFoundError,
)
from gandi_mcp.files.work_directory import WorkDirectory
from gandi_mcp.files.written_file import WrittenFile


@dataclass
class InMemoryWorkDirectory(WorkDirectory):
    """Files by relative path; ``private`` lists the files written as private."""

    files: dict[str, str] = field(default_factory=dict)
    private: set[str] = field(default_factory=set)

    def check_target(self, relative_path: str, *, overwrite: bool = False) -> str:
        if relative_path.startswith(("/", "\\")) or ".." in relative_path.split("/"):
            raise OutsideWorkDirectoryError("outside")
        if relative_path in self.files and not overwrite:
            raise FileExistsInWorkDirectoryError("exists")
        return relative_path

    def write(
        self, relative_path: str, content: str, *, overwrite: bool = False, private: bool = False
    ) -> WrittenFile:
        relative = self.check_target(relative_path, overwrite=overwrite)
        self.files[relative] = content
        if private:
            self.private.add(relative)
        return WrittenFile(relative, f"/work/{relative}", len(content.encode("utf-8")))

    def read(self, relative_path: str, max_bytes: int) -> str:
        if relative_path not in self.files:
            raise WorkFileNotFoundError("missing")
        content = self.files[relative_path]
        if len(content.encode("utf-8")) > max_bytes:
            raise FileTooLargeError("too large")
        return content
