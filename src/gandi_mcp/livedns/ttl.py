# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the TTL of a record."""

from dataclasses import dataclass

from gandi_mcp.livedns.exceptions import InvalidRecordError

MIN_TTL = 300
MAX_TTL = 2_592_000


@dataclass(frozen=True)
class Ttl:
    """How long a resolver may cache a record, in seconds (300 to 2592000)."""

    seconds: int

    def __post_init__(self) -> None:
        if isinstance(self.seconds, bool) or not MIN_TTL <= self.seconds <= MAX_TTL:
            raise InvalidRecordError(f"a TTL is between {MIN_TTL} and {MAX_TTL} seconds")
