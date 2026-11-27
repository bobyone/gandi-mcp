# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value objects of the identifiers Gandi gives LiveDNS resources."""

import re
from dataclasses import dataclass

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError

IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def _checked(value: str, what: str) -> str:
    cleaned = value.strip()
    if not IDENTIFIER.match(cleaned):
        raise InvalidLiveDnsInputError(f"not a {what} identifier")
    return cleaned


@dataclass(frozen=True)
class SnapshotId:
    """The identifier of a snapshot, as returned by the list of snapshots."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _checked(self.value, "snapshot"))


@dataclass(frozen=True)
class SigningKeyId:
    """The identifier of a signing key of a zone."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _checked(self.value, "signing key"))


@dataclass(frozen=True)
class TsigKeyId:
    """The identifier of a TSIG key of the account."""

    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _checked(self.value, "TSIG key"))
