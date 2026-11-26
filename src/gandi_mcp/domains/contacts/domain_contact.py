# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a domain contact given by the user (owner, admin, tech, bill)."""

import re
import unicodedata
from dataclasses import asdict, dataclass
from enum import StrEnum

from gandi_mcp.domains.contacts.exceptions import InvalidContactError
from gandi_mcp.gandi.gandi_response import JsonValue

MAX_FIELD_LENGTH = 280
MAX_EMAIL_LENGTH = 254
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE = re.compile(r"^\+\d{1,3}\.\d{4,14}$")
COUNTRY = re.compile(r"^[A-Z]{2}$")


class ContactType(StrEnum):
    """Kinds of contacts Gandi accepts."""

    INDIVIDUAL = "individual"
    COMPANY = "company"
    ASSOCIATION = "association"
    PUBLIC_BODY = "publicbody"


def _text(name: str, value: str | None, *, required: bool) -> str | None:
    if value is None or not value.strip():
        if required:
            raise InvalidContactError(f"{name} is required")
        return None
    cleaned = unicodedata.normalize("NFC", " ".join(value.split()))
    if len(cleaned) > MAX_FIELD_LENGTH:
        raise InvalidContactError(f"{name} has at most {MAX_FIELD_LENGTH} characters")
    if any(unicodedata.category(character).startswith("C") for character in cleaned):
        raise InvalidContactError(f"{name} has a control character")
    return cleaned


@dataclass(frozen=True)
class DomainContact:
    """The Gandi contact fields this project supports, validated and bounded.

    ``orgname`` is required for any type but ``individual``. Privacy options default
    to hiding the contact in the WHOIS. Personal data: never logged.
    """

    type: ContactType
    given: str
    family: str
    email: str
    streetaddr: str
    city: str
    zip: str
    country: str
    phone: str | None = None
    orgname: str | None = None
    state: str | None = None
    data_obfuscated: bool = True
    mail_obfuscated: bool = True

    def __post_init__(self) -> None:
        for name in ("given", "family", "streetaddr", "city", "zip"):
            object.__setattr__(self, name, _text(name, getattr(self, name), required=True))
        for name in ("orgname", "state"):
            object.__setattr__(self, name, _text(name, getattr(self, name), required=False))
        email = self.email.strip()
        if len(email) > MAX_EMAIL_LENGTH or not EMAIL.match(email):
            raise InvalidContactError("email is not an email address")
        object.__setattr__(self, "email", email)
        country = self.country.strip().upper()
        if not COUNTRY.match(country):
            raise InvalidContactError("country is a two-letter ISO 3166 code")
        object.__setattr__(self, "country", country)
        if self.phone is not None and not PHONE.match(self.phone.strip()):
            raise InvalidContactError("phone is written +<country code>.<number>")
        if self.type is not ContactType.INDIVIDUAL and self.orgname is None:
            raise InvalidContactError("orgname is required for an organization")

    def __repr__(self) -> str:
        return f"DomainContact(type={self.type.value}, country={self.country})"

    def to_json(self) -> dict[str, JsonValue]:
        """The contact as Gandi expects it; absent optional fields are left out."""
        fields = asdict(self)
        fields["type"] = self.type.value
        return {key: value for key, value in fields.items() if value is not None}
