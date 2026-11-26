# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value objects of the domain settings the user changes."""

import base64
import binascii
import ipaddress
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.exceptions import InvalidDomainInputError, InvalidDomainNameError

MAX_TAG_LENGTH = 100
MAX_URL_LENGTH = 2048
MAX_PUBLIC_KEY_LENGTH = 4096
MAX_EMAIL_LENGTH = 254
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
KEY_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


@dataclass(frozen=True)
class IpAddress:
    """An IPv4 or IPv6 address, in its compressed form."""

    value: str

    def __post_init__(self) -> None:
        try:
            address = ipaddress.ip_address(self.value.strip())
        except ValueError as error:
            raise InvalidDomainInputError("not an IP address") from error
        object.__setattr__(self, "value", address.compressed)


class DnssecKeyType(StrEnum):
    """Kinds of DNSSEC keys."""

    NONE = "none"
    ZSK = "zsk"
    KSK = "ksk"


@dataclass(frozen=True)
class DnssecKeySpec:
    """A DNSSEC key to publish: algorithm number, type and base64 public key."""

    algorithm: int
    type: DnssecKeyType
    public_key: str

    def __post_init__(self) -> None:
        if isinstance(self.algorithm, bool) or not 0 <= self.algorithm <= 255:  # noqa: PLR2004
            raise InvalidDomainInputError("a DNSSEC algorithm is between 0 and 255")
        key = "".join(self.public_key.split())
        if not key or len(key) > MAX_PUBLIC_KEY_LENGTH:
            raise InvalidDomainInputError("a public key has 1 to 4096 characters")
        try:
            base64.b64decode(key, validate=True)
        except (binascii.Error, ValueError) as error:
            raise InvalidDomainInputError("a public key is written in base64") from error
        object.__setattr__(self, "public_key", key)

    def to_json(self) -> dict[str, str | int]:
        """The key as Gandi expects it."""
        return {"algorithm": self.algorithm, "type": self.type.value, "public_key": self.public_key}


@dataclass(frozen=True)
class DnssecKeyId:
    """The identifier Gandi gives a DNSSEC key."""

    value: str

    def __post_init__(self) -> None:
        if not KEY_ID.match(self.value.strip()):
            raise InvalidDomainInputError("not a DNSSEC key identifier")
        object.__setattr__(self, "value", self.value.strip())


@dataclass(frozen=True)
class TagName:
    """A tag: 1 to 100 printable characters."""

    value: str

    def __post_init__(self) -> None:
        cleaned = unicodedata.normalize("NFC", " ".join(self.value.split()))
        if not cleaned or len(cleaned) > MAX_TAG_LENGTH:
            raise InvalidDomainInputError(f"a tag has 1 to {MAX_TAG_LENGTH} characters")
        if any(unicodedata.category(character).startswith("C") for character in cleaned):
            raise InvalidDomainInputError("a tag has no control character")
        object.__setattr__(self, "value", cleaned)


@dataclass(frozen=True)
class RedirectionUrl:
    """An http or https target URL with a valid host name."""

    value: str

    def __post_init__(self) -> None:
        url = self.value.strip()
        if len(url) > MAX_URL_LENGTH:
            raise InvalidDomainInputError("a URL has at most 2048 characters")
        parts = urlsplit(url)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            raise InvalidDomainInputError("a redirection target is an http or https URL")
        if any(character.isspace() or ord(character) < 32 for character in url):  # noqa: PLR2004
            raise InvalidDomainInputError("a URL has no space nor control character")
        try:
            DomainName(parts.hostname)
        except InvalidDomainNameError as error:
            raise InvalidDomainInputError("the URL host is not a domain name") from error
        object.__setattr__(self, "value", url)


@dataclass(frozen=True)
class EmailAddress:
    """An email address, to resend a confirmation email to."""

    value: str

    def __post_init__(self) -> None:
        email = self.value.strip()
        if len(email) > MAX_EMAIL_LENGTH or not EMAIL.match(email):
            raise InvalidDomainInputError("not an email address")
        object.__setattr__(self, "value", email)
