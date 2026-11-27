# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the work directory notion."""


class WorkDirectoryError(Exception):
    """Base class of the work directory errors (also: a file cannot be read or written)."""


class OutsideWorkDirectoryError(WorkDirectoryError):
    """A path is absolute, goes up with ``..``, or leads out of the work directory."""


class FileExistsInWorkDirectoryError(WorkDirectoryError):
    """The file already exists and overwriting it was not asked."""


class FileTooLargeError(WorkDirectoryError):
    """The file to read is larger than allowed."""


class WorkFileNotFoundError(WorkDirectoryError):
    """The file to read does not exist in the work directory."""


class UnreadableWorkFileError(WorkDirectoryError):
    """The file to read is not UTF-8 text."""
