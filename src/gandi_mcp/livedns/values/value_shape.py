# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Simple shape checks of record values, per type (strategy)."""

import ipaddress
import re
from collections.abc import Callable, Mapping

from gandi_mcp.livedns.exceptions import InvalidRecordError
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.record_value import RecordValue

MAX_UINT16 = 65535
# A host name as a record value: relative (``mail``), absolute (``mail.example.com.``)
# or the zone itself (``@``). Labels are separated by a mandatory dot, so that a name
# splits into labels in one way only: no catastrophic backtracking.
LABEL = r"[A-Za-z0-9_*](?:[A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?"
HOST = re.compile(rf"^(?:@|\.|{LABEL}(?:\.{LABEL})*\.?)$")


def _uint16(text: str) -> bool:
    return text.isdigit() and int(text) <= MAX_UINT16


def _host(text: str) -> bool:
    return len(text) <= 255 and HOST.match(text) is not None  # noqa: PLR2004 - DNS limit


def _ipv4(text: str) -> bool:
    try:
        ipaddress.IPv4Address(text)
    except ValueError:
        return False
    return True


def _ipv6(text: str) -> bool:
    try:
        ipaddress.IPv6Address(text)
    except ValueError:
        return False
    return True


def _mx(text: str) -> bool:
    parts = text.split()
    return len(parts) == 2 and _uint16(parts[0]) and _host(parts[1])  # noqa: PLR2004


def _srv(text: str) -> bool:
    parts = text.split()
    return (
        len(parts) == 4  # noqa: PLR2004 - priority, weight, port, target
        and all(_uint16(part) for part in parts[:3])
        and _host(parts[3])
    )


SHAPES: Mapping[RecordType, Callable[[str], bool]] = {
    RecordType.A: _ipv4,
    RecordType.AAAA: _ipv6,
    RecordType.CNAME: _host,
    RecordType.NS: _host,
    RecordType.MX: _mx,
    RecordType.SRV: _srv,
}


def check_shape(record_type: RecordType, value: RecordValue) -> None:
    """Refuse a value whose shape does not fit its type, for the common types.

    Only A, AAAA, CNAME, NS, MX and SRV are checked here; Gandi judges the others.

    Raises:
        InvalidRecordError: if the value does not have the shape of its type.
    """
    shape = SHAPES.get(record_type)
    if shape is not None and not shape(value.value):
        raise InvalidRecordError(f"not a valid {record_type.value} value")
