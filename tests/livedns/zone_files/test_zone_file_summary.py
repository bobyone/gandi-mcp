# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the record count of a zone file."""

from gandi_mcp.livedns.zone_files.zone_file_summary import record_count

ZONE = """$ORIGIN example.com.
$TTL 10800
; exported by LiveDNS
@ 10800 IN SOA ns1.gandi.net. hostmaster.gandi.net. (
    1700000000 ; serial
    10800 3600 604800 10800 )

@ 10800 IN A 192.0.2.1
www 10800 IN CNAME @  ; the web site
@ 10800 IN TXT "v=spf1 include:_mailcust.gandi.net ?all"
"""


def test_records_are_counted_once_each() -> None:
    assert record_count(ZONE) == 4


def test_an_empty_zone_has_no_record() -> None:
    assert record_count("") == 0
    assert record_count("; nothing\n\n$TTL 300\n") == 0
