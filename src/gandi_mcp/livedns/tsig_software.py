# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a DNS server software of a TSIG configuration sample."""

from enum import StrEnum

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError


class TsigSoftware(StrEnum):
    """The secondary server software Gandi gives a configuration sample for."""

    BIND = "bind"
    KNOT = "knot"
    NSD = "nsd"
    POWERDNS = "powerdns"

    @classmethod
    def parse(cls, value: str) -> "TsigSoftware":
        """Read a software name, whatever its case.

        Raises:
            InvalidLiveDnsInputError: if Gandi gives no sample for this software.
        """
        try:
            return cls(value.strip().lower())
        except ValueError:
            raise InvalidLiveDnsInputError("no configuration sample for this software") from None
