# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the kind of a signing key."""

from enum import IntEnum

from gandi_mcp.livedns.exceptions import InvalidLiveDnsInputError


class SigningKeyFlag(IntEnum):
    """The DNSSEC flags LiveDNS accepts for a new signing key."""

    ZSK = 256
    KSK = 257

    @classmethod
    def parse(cls, value: int) -> "SigningKeyFlag":
        """Read a flag: 256 (zone signing key) or 257 (key signing key).

        Raises:
            InvalidLiveDnsInputError: for any other value.
        """
        try:
            return cls(value)
        except ValueError:
            raise InvalidLiveDnsInputError("a signing key flag is 256 (ZSK) or 257 (KSK)") from None
