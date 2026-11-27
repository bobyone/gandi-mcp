# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a record name, relative to its zone."""

import re
from dataclasses import dataclass

import idna

from gandi_mcp.livedns.exceptions import InvalidRecordError

APEX = "@"
WILDCARD = "*"
MAX_NAME_LENGTH = 253
# Host names, and service labels such as ``_dmarc`` or ``_acme-challenge``.
ASCII_LABEL = re.compile(r"^[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?$")


def _label(label: str) -> str:
    lowered = label.lower()
    if ASCII_LABEL.match(lowered):
        return lowered
    try:
        encoded = idna.encode(label, uts46=True).decode("ascii")
    except (idna.IDNAError, UnicodeError):
        raise InvalidRecordError("not a valid record name") from None
    if "." in encoded or not ASCII_LABEL.match(encoded):
        raise InvalidRecordError("not a valid record name")
    return encoded


@dataclass(frozen=True)
class RecordName:
    """A name in a zone: ``@`` for the zone itself, ``www``, ``*.dev``, ``_dmarc``.

    The name is relative to the zone, without a trailing dot. ``value`` is its ASCII
    form (internationalized labels in IDNA form, lower case), sent to Gandi; a
    wildcard ``*`` is only allowed as the first label.
    """

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if cleaned == APEX:
            object.__setattr__(self, "value", APEX)
            return
        if not cleaned or cleaned.endswith(".") or len(cleaned) > MAX_NAME_LENGTH:
            raise InvalidRecordError("a record name is relative to its zone, e.g. www or @")
        labels = cleaned.split(".")
        converted = [
            WILDCARD if index == 0 and label == WILDCARD else _label(label)
            for index, label in enumerate(labels)
        ]
        ascii_form = ".".join(converted)
        if len(ascii_form) > MAX_NAME_LENGTH:
            raise InvalidRecordError("a record name has at most 253 characters")
        object.__setattr__(self, "value", ascii_form)

    def __str__(self) -> str:
        return self.value
