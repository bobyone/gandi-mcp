# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the name of a snapshot."""

from dataclasses import dataclass

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError

MAX_SNAPSHOT_NAME_LENGTH = 255
FIRST_PRINTABLE = 32


@dataclass(frozen=True)
class SnapshotName:
    """A name chosen for a snapshot: 1 to 255 characters, no control character."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if (
            not cleaned
            or len(cleaned) > MAX_SNAPSHOT_NAME_LENGTH
            or any(ord(character) < FIRST_PRINTABLE for character in cleaned)
        ):
            raise InvalidLiveDnsInputError("a snapshot name has 1 to 255 characters")
        object.__setattr__(self, "value", cleaned)
