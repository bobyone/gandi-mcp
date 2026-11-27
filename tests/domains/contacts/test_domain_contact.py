# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the domain contacts given by the user."""

from dataclasses import replace

import pytest

from gandi_mcp.domains.contacts.domain_contact import ContactType, DomainContact
from gandi_mcp.domains.contacts.exceptions import InvalidContactError

ADA = DomainContact(
    type=ContactType.INDIVIDUAL,
    given=" Ada ",
    family="Lovelace",
    email="ada@example.org",
    streetaddr="1 rue  de Paris",
    city="Paris",
    zip="75001",
    country="fr",
    phone="+33.123456789",
)


def test_cleans_and_serializes() -> None:
    assert ADA.given == "Ada"
    assert ADA.streetaddr == "1 rue de Paris"
    assert ADA.to_json() == {
        "type": "individual",
        "given": "Ada",
        "family": "Lovelace",
        "email": "ada@example.org",
        "streetaddr": "1 rue de Paris",
        "city": "Paris",
        "zip": "75001",
        "country": "FR",
        "phone": "+33.123456789",
        "data_obfuscated": True,
        "mail_obfuscated": True,
    }
    assert "Lovelace" not in repr(ADA)


@pytest.mark.parametrize(
    "changes",
    [
        {"given": " "},
        {"family": "x" * 281},
        {"city": "Paris\x07"},
        {"email": "not-an-email"},
        {"country": "FRA"},
        {"phone": "0123456789"},
        {"type": ContactType.COMPANY},
    ],
)
def test_invalid_contacts(changes: dict[str, object]) -> None:
    with pytest.raises(InvalidContactError):
        replace(ADA, **changes)  # type: ignore[arg-type]


def test_an_organization_needs_its_name() -> None:
    company = replace(ADA, type=ContactType.COMPANY, orgname="Ada Corp")

    assert company.to_json()["orgname"] == "Ada Corp"
