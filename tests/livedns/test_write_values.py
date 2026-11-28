# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the values written to LiveDNS: TTL, record values, records, snapshots, keys."""

import time

import pytest

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError, InvalidRecordError
from gandi_mcp.livedns.record import Record, record_values
from gandi_mcp.livedns.record_type import RecordType
from gandi_mcp.livedns.record_value import RecordValue
from gandi_mcp.livedns.signing_key_flag import SigningKeyFlag
from gandi_mcp.livedns.snapshot_name import SnapshotName
from gandi_mcp.livedns.ttl import Ttl


@pytest.mark.parametrize("seconds", [300, 3600, 2_592_000])
def test_ttl_bounds_are_accepted(seconds: int) -> None:
    assert Ttl(seconds).seconds == seconds


@pytest.mark.parametrize("seconds", [299, 0, -1, 2_592_001, True])
def test_ttl_out_of_bounds_is_refused(seconds: int) -> None:
    with pytest.raises(InvalidRecordError):
        Ttl(seconds)


def test_record_values_are_trimmed_printable_ascii() -> None:
    assert RecordValue('  "v=spf1 -all" ').value == '"v=spf1 -all"'
    assert str(RecordValue("x" * 16384)) == "x" * 16384


@pytest.mark.parametrize("value", ["", "   ", "a\nb", "tab\there", "café", "x" * 16385, "\x00"])
def test_invalid_record_values_are_refused(value: str) -> None:
    with pytest.raises(InvalidRecordError):
        RecordValue(value)


@pytest.mark.parametrize(
    ("record_type", "value"),
    [
        ("A", "192.0.2.1"),
        ("AAAA", "2001:db8::1"),
        ("CNAME", "www.example.com."),
        ("CNAME", "@"),
        ("NS", "ns1.gandi.net."),
        ("MX", "10 spool.mail.gandi.net."),
        ("SRV", "0 1 443 _sip.example.com."),
        ("SRV", "0 0 0 ."),
        ("TXT", '"anything goes"'),
        ("CAA", '0 issue "letsencrypt.org"'),
    ],
)
def test_values_of_the_right_shape_are_accepted(record_type: str, value: str) -> None:
    assert record_values(RecordType.parse(record_type), [value])[0].value == value


@pytest.mark.parametrize(
    ("record_type", "value"),
    [
        ("A", "2001:db8::1"),
        ("A", "300.1.1.1"),
        ("AAAA", "192.0.2.1"),
        ("CNAME", "two words"),
        ("NS", "-bad-.example."),
        ("MX", "mail.example.com."),
        ("MX", "70000 mail.example.com."),
        ("SRV", "0 0 mail.example.com."),
        ("CNAME", "a..b"),
        ("CNAME", "a-"),
        ("CNAME", "a" * 64),
    ],
)
def test_values_of_the_wrong_shape_are_refused(record_type: str, value: str) -> None:
    with pytest.raises(InvalidRecordError):
        record_values(RecordType.parse(record_type), [value])


@pytest.mark.parametrize("value", ["*" + "00" * 127 + "!", "a" * 254 + "!", "a." * 127 + "!"])
def test_a_long_malformed_host_is_refused_quickly(value: str) -> None:
    started = time.perf_counter()

    with pytest.raises(InvalidRecordError):
        record_values(RecordType.CNAME, [value])

    assert time.perf_counter() - started < 0.5


def test_duplicate_values_are_merged_and_counts_bounded() -> None:
    assert len(record_values(RecordType.A, ["192.0.2.1", " 192.0.2.1"])) == 1
    with pytest.raises(InvalidRecordError):
        record_values(RecordType.A, [])
    with pytest.raises(InvalidRecordError):
        record_values(RecordType.TXT, [f'"{index}"' for index in range(101)])


def test_a_record_is_written_as_gandi_expects() -> None:
    record = Record.of("WWW", "cname", ["@"], 600)

    assert record.to_json() == {
        "rrset_name": "www",
        "rrset_type": "CNAME",
        "rrset_values": ["@"],
        "rrset_ttl": 600,
    }
    assert Record.of("@", "A", ["192.0.2.1"]).values_json() == {"rrset_values": ["192.0.2.1"]}


def test_snapshot_names_are_bounded() -> None:
    assert SnapshotName("  before migration ").value == "before migration"
    for name in ["", "  ", "x" * 256, "line\nbreak"]:
        with pytest.raises(InvalidLiveDnsInputError):
            SnapshotName(name)


def test_signing_key_flags() -> None:
    assert SigningKeyFlag.parse(257) is SigningKeyFlag.KSK
    with pytest.raises(InvalidLiveDnsInputError):
        SigningKeyFlag.parse(255)
