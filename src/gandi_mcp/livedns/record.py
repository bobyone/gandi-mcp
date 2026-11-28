# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a record: the values of one name and one type, with their TTL."""

from collections.abc import Sequence
from dataclasses import dataclass

from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.livedns.exceptions import InvalidRecordError
from gandi_mcp.livedns.record_name import RecordName
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.record_value import RecordValue
from gandi_mcp.livedns.ttl import Ttl
from gandi_mcp.livedns.values.value_shape import check_shape

MAX_VALUES = 100


def record_values(record_type: RecordType, values: Sequence[str]) -> tuple[RecordValue, ...]:
    """Validate the values of a record of ``record_type``, without duplicates.

    Raises:
        InvalidRecordError: if there is no value, more than 100, or an invalid one.
    """
    checked = tuple(dict.fromkeys(RecordValue(value) for value in values))
    if not 1 <= len(checked) <= MAX_VALUES:
        raise InvalidRecordError(f"a record has 1 to {MAX_VALUES} values")
    for value in checked:
        check_shape(record_type, value)
    return checked


@dataclass(frozen=True)
class Record:
    """A record (an RRset in the Gandi API): a name and type pair is unique in a zone.

    Attributes:
        name: Name relative to the zone.
        type: Record type.
        values: 1 to 100 distinct values, checked for their type.
        ttl: TTL, or ``None`` for the default of LiveDNS.
    """

    name: RecordName
    type: RecordType
    values: tuple[RecordValue, ...]
    ttl: Ttl | None = None

    @classmethod
    def of(
        cls, name: str, record_type: str, values: Sequence[str], ttl: int | None = None
    ) -> "Record":
        """Build a record from raw input.

        Raises:
            InvalidRecordError: if the name, type, a value or the TTL is not valid.
        """
        kind = RecordType.parse(record_type)
        return cls(
            RecordName(name),
            kind,
            record_values(kind, values),
            Ttl(ttl) if ttl is not None else None,
        )

    def values_json(self) -> dict[str, JsonValue]:
        """``rrset_values`` and, when given, ``rrset_ttl``."""
        body: dict[str, JsonValue] = {"rrset_values": [value.value for value in self.values]}
        if self.ttl is not None:
            body["rrset_ttl"] = self.ttl.seconds
        return body

    def to_json(self) -> dict[str, JsonValue]:
        """The record as an item of a zone or of the records of a name."""
        return {"rrset_name": self.name.value, "rrset_type": self.type.value, **self.values_json()}
