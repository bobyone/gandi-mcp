# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a record type."""

from enum import StrEnum

from gandi_mcp.livedns.exceptions import InvalidRecordError


class RecordType(StrEnum):
    """The record types the LiveDNS API documents for a record."""

    A = "A"
    AAAA = "AAAA"
    ALIAS = "ALIAS"
    CAA = "CAA"
    CDS = "CDS"
    CNAME = "CNAME"
    DNAME = "DNAME"
    DS = "DS"
    HTTPS = "HTTPS"
    KEY = "KEY"
    LOC = "LOC"
    MX = "MX"
    NAPTR = "NAPTR"
    NS = "NS"
    OPENPGPKEY = "OPENPGPKEY"
    PTR = "PTR"
    RP = "RP"
    SOA = "SOA"
    SPF = "SPF"
    SRV = "SRV"
    SSHFP = "SSHFP"
    SVCB = "SVCB"
    TLSA = "TLSA"
    TXT = "TXT"
    WKS = "WKS"

    @classmethod
    def parse(cls, value: str) -> "RecordType":
        """Read a type, whatever its case.

        Raises:
            InvalidRecordError: if LiveDNS does not support this type.
        """
        try:
            return cls(value.strip().upper())
        except ValueError:
            raise InvalidRecordError("not a record type supported by LiveDNS") from None
