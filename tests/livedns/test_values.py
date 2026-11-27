# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the record type, identifier and TSIG software value objects."""

import pytest

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError, InvalidRecordError
from gandi_mcp.livedns.identifiers import SigningKeyId, SnapshotId, TsigKeyId
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.tsig_software import TsigSoftware


def test_record_types_are_read_whatever_their_case() -> None:
    assert RecordType.parse(" mx ") is RecordType.MX
    assert RecordType.parse("Https") is RecordType.HTTPS


@pytest.mark.parametrize("given", ["", "MX/../A", "AXFR", "ANY"])
def test_unknown_record_types_are_refused(given: str) -> None:
    with pytest.raises(InvalidRecordError):
        RecordType.parse(given)


@pytest.mark.parametrize("kind", [SnapshotId, SigningKeyId, TsigKeyId])
def test_identifiers_are_trimmed(kind: type[SnapshotId | SigningKeyId | TsigKeyId]) -> None:
    identifier = " 7d6a3a3e-1b2c-4d5e-8f90-0123456789ab "

    assert kind(identifier).value == identifier.strip()


@pytest.mark.parametrize("kind", [SnapshotId, SigningKeyId, TsigKeyId])
@pytest.mark.parametrize("given", ["", "a/b", "..", "x" * 65, "id?x=1", "a b"])
def test_invalid_identifiers_are_refused(
    kind: type[SnapshotId | SigningKeyId | TsigKeyId], given: str
) -> None:
    with pytest.raises(InvalidLiveDnsInputError):
        kind(given)


def test_tsig_software_is_read_whatever_its_case() -> None:
    assert TsigSoftware.parse("PowerDNS") is TsigSoftware.POWERDNS


def test_unknown_tsig_software_is_refused() -> None:
    with pytest.raises(InvalidLiveDnsInputError):
        TsigSoftware.parse("unbound")
