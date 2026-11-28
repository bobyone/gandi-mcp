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
@ 10800 IN MX 10 spool.mail.gandi.net.
@ 10800 IN MX 50 fb.mail.gandi.net.
www 10800 IN CNAME @  ; the web site
@ 10800 IN TXT "v=spf1 include:_mailcust.gandi.net ?all"
    IN TXT "google-site-verification=abc"
_imap._tcp 10800 IN SRV 0 0 0 .
MAIL IN A 192.0.2.2
mail 300 A 192.0.2.3
"""


def test_records_are_name_and_type_pairs() -> None:
    # @ A, @ MX (two values), www CNAME, @ TXT (two lines), SRV, mail A (twice); no SOA.
    assert record_count(ZONE) == 6


def test_an_empty_zone_has_no_record() -> None:
    assert record_count("") == 0
    assert record_count("; nothing\n\n$TTL 300\n") == 0
    assert record_count("www 300 IN\n") == 0
