# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a file written to the work directory."""

from dataclasses import dataclass


@dataclass(frozen=True)
class WrittenFile:
    """What was written: shown to the model instead of the content.

    Attributes:
        relative_path: Path relative to the work directory, with ``/`` separators.
        absolute_path: Full path on this computer, for the user.
        size: Size in bytes.
    """

    relative_path: str
    absolute_path: str
    size: int
