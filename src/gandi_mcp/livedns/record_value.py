# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of one value of a record."""

import re
from dataclasses import dataclass

from gandi_mcp.livedns.exceptions import InvalidRecordError

MAX_VALUE_LENGTH = 16384
# The values LiveDNS accepts: printable ASCII only, no control character nor newline.
PRINTABLE_ASCII = re.compile(r"^[\x20-\x7E]+$")


@dataclass(frozen=True)
class RecordValue:
    """One value of a record, as LiveDNS writes it (``192.0.2.1``, ``10 mx.example.``).

    Printable ASCII, 1 to 16384 characters; surrounding spaces are removed. TXT
    values keep their quotes as given.
    """

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned or len(cleaned) > MAX_VALUE_LENGTH or not PRINTABLE_ASCII.match(cleaned):
            raise InvalidRecordError(
                f"a record value has 1 to {MAX_VALUE_LENGTH} printable ASCII characters"
            )
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value
