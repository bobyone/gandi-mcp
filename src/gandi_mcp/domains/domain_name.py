# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value objects of domain, host and TLD names (IDNA 2008, UTS 46 mapping)."""

from dataclasses import dataclass, field

import idna

from gandi_mcp.domains.exceptions import InvalidDomainNameError

MAX_NAME_LENGTH = 253
MAX_LABEL_LENGTH = 63


def to_ascii(name: str, *, labels: int) -> tuple[str, str]:
    """Return the ASCII and Unicode forms of a name with at least ``labels`` labels.

    Raises:
        InvalidDomainNameError: if the name is empty, too long, or not IDNA 2008 valid.
    """
    cleaned = name.strip().rstrip(".")
    if not cleaned or len(cleaned) > MAX_NAME_LENGTH:
        raise InvalidDomainNameError("a name has 1 to 253 characters")
    try:
        ascii_form = idna.encode(cleaned, uts46=True).decode("ascii")
        unicode_form = idna.decode(ascii_form)
    except (idna.IDNAError, UnicodeError) as error:
        raise InvalidDomainNameError("not a valid domain name") from error
    parts = ascii_form.split(".")
    if len(parts) < labels or len(ascii_form) > MAX_NAME_LENGTH:
        raise InvalidDomainNameError("not a valid domain name")
    return ascii_form, unicode_form


@dataclass(frozen=True)
class DomainName:
    """A fully qualified domain name such as ``example.com`` or ``bücher.de``.

    ``value`` is the ASCII form sent to Gandi; ``unicode`` is the readable form.
    Two names are equal when their ASCII forms are.
    """

    value: str
    unicode: str = field(init=False, compare=False)

    def __post_init__(self) -> None:
        ascii_form, unicode_form = to_ascii(self.value, labels=2)
        object.__setattr__(self, "value", ascii_form)
        object.__setattr__(self, "unicode", unicode_form)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TldName:
    """An extension such as ``fr`` or ``com``, without its leading dot."""

    value: str

    def __post_init__(self) -> None:
        ascii_form, _ = to_ascii(self.value.lstrip("."), labels=1)
        if "." in ascii_form:
            raise InvalidDomainNameError("an extension is a single label")
        object.__setattr__(self, "value", ascii_form)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class HostLabel:
    """A host relative to a domain, such as ``ns1`` or ``@`` for the domain itself."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if cleaned == "@":
            object.__setattr__(self, "value", cleaned)
            return
        ascii_form, _ = to_ascii(cleaned, labels=1)
        object.__setattr__(self, "value", ascii_form)

    def __str__(self) -> str:
        return self.value
