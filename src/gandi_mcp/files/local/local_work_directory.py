# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Work directory on the local file system."""

import logging
import os
import stat
from pathlib import Path, PurePosixPath, PureWindowsPath

from gandi_mcp.files.exceptions import (
    FileExistsInWorkDirectoryError,
    FileTooLargeError,
    OutsideWorkDirectoryError,
    UnreadableWorkFileError,
    WorkDirectoryError,
    WorkFileNotFoundError,
)
from gandi_mcp.files.work_directory import WorkDirectory
from gandi_mcp.files.written_file import WrittenFile

MAX_RELATIVE_LENGTH = 255
# Characters Windows refuses in a file name (``:`` would also open an alternate stream).
FIRST_PRINTABLE = 32
FORBIDDEN_CHARACTERS = frozenset(':*?"<>|')
PRIVATE_MODE = 0o600
DEFAULT_MODE = 0o644
DIRECTORY_MODE = 0o700

logger = logging.getLogger(__name__)


def _parts(relative_path: str) -> tuple[str, ...]:
    """Split a relative path given with ``/`` or backslash separators.

    Raises:
        OutsideWorkDirectoryError: if the path is empty, absolute, has a drive, goes
            up with ``..`` or holds a character that is not allowed in a file name.
    """
    text = relative_path.strip()
    windows = PureWindowsPath(text)
    if (
        not text
        or len(text) > MAX_RELATIVE_LENGTH
        or windows.drive
        or windows.root
        or PurePosixPath(text).is_absolute()
    ):
        raise OutsideWorkDirectoryError("give a path relative to the work directory")
    parts = tuple(part for part in text.replace("\\", "/").split("/") if part not in ("", "."))
    if not parts or any(
        part == ".."
        or part != part.strip()
        or any(
            ord(character) < FIRST_PRINTABLE or character in FORBIDDEN_CHARACTERS
            for character in part
        )
        for part in parts
    ):
        raise OutsideWorkDirectoryError("give a path relative to the work directory")
    return parts


class LocalWorkDirectory(WorkDirectory):
    """A directory of this computer, created on first write with owner-only access.

    Every path is resolved (symbolic links followed) and must stay inside the
    directory. A file is created exclusively unless overwriting is asked; a private
    file gets the mode 0600 on POSIX systems (on Windows, the permissions inherited
    from the user profile apply).
    """

    def __init__(self, root: Path) -> None:
        """``root`` is the configured directory (``files.work_directory``)."""
        self._root = root

    def check_target(self, relative_path: str, *, overwrite: bool = False) -> str:
        parts, target = self._resolve(relative_path)
        if target.is_dir():
            raise FileExistsInWorkDirectoryError("a directory has this name")
        if target.exists() and not overwrite:
            raise FileExistsInWorkDirectoryError("the file already exists")
        return "/".join(parts)

    def write(
        self, relative_path: str, content: str, *, overwrite: bool = False, private: bool = False
    ) -> WrittenFile:
        relative = self.check_target(relative_path, overwrite=overwrite)
        data = content.encode("utf-8")
        try:
            self._root.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
            _, target = self._resolve(relative_path)
            target.parent.mkdir(mode=DIRECTORY_MODE, parents=True, exist_ok=True)
            # Resolved again: a symbolic link may have appeared in the meantime.
            _, target = self._resolve(relative_path)
            flags = os.O_WRONLY | os.O_CREAT | getattr(os, "O_BINARY", 0)
            flags |= os.O_TRUNC if overwrite else os.O_EXCL
            descriptor = os.open(target, flags, PRIVATE_MODE if private else DEFAULT_MODE)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
            if private and os.name == "posix":
                target.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except FileExistsError as error:
            raise FileExistsInWorkDirectoryError("the file already exists") from error
        except OSError as error:
            logger.warning("cannot write a file of the work directory: %s", error.strerror)
            raise WorkDirectoryError("the file cannot be written") from error
        return WrittenFile(relative, str(target), len(data))

    def read(self, relative_path: str, max_bytes: int) -> str:
        _, target = self._resolve(relative_path)
        if not target.is_file():
            raise WorkFileNotFoundError("no such file in the work directory")
        try:
            if target.stat().st_size > max_bytes:
                raise FileTooLargeError(f"the file is larger than {max_bytes} bytes")
            with target.open("rb") as stream:
                data = stream.read(max_bytes + 1)
        except OSError as error:
            logger.warning("cannot read a file of the work directory: %s", error.strerror)
            raise WorkDirectoryError("the file cannot be read") from error
        if len(data) > max_bytes:
            raise FileTooLargeError(f"the file is larger than {max_bytes} bytes")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            raise UnreadableWorkFileError("the file is not UTF-8 text") from None

    def _resolve(self, relative_path: str) -> tuple[tuple[str, ...], Path]:
        parts = _parts(relative_path)
        root = self._root.resolve()
        target = root.joinpath(*parts).resolve()
        if target == root or not target.is_relative_to(root):
            raise OutsideWorkDirectoryError("the path leads out of the work directory")
        return parts, target
