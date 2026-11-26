# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the minimization of contacts and authorization codes."""

from gandi_mcp.domains.contacts.contact_redactor import HIDDEN, ContactRedactor
from gandi_mcp.gandi.gandi_response import JsonValue

OWNER: JsonValue = {
    "type": "individual",
    "country": "FR",
    "given": "Ada",
    "family": "Lovelace",
    "email": "ada@example.org",
    "streetaddr": "1 rue de Paris",
    "phone": "+33.123456789",
}
DETAILS: JsonValue = {
    "fqdn": "example.com",
    "authinfo": "S3cret-Code",
    "contacts": {
        "owner": OWNER,
        "tech": {
            "type": "company",
            "country": "DE",
            "email": "t@example.org",
            "same_as_owner": False,
        },
    },
    "nameservers": ["ns1.gandi.net"],
}


def test_contacts_and_code_are_hidden_by_default() -> None:
    filtered = ContactRedactor().apply(DETAILS)

    assert filtered == {
        "fqdn": "example.com",
        "authinfo": HIDDEN,
        "contacts": {
            "owner": {"type": "individual", "country": "FR", "details": HIDDEN},
            "tech": {
                "type": "company",
                "country": "DE",
                "same_as_owner": False,
                "details": HIDDEN,
            },
        },
        "nameservers": ["ns1.gandi.net"],
    }
    text = str(filtered)
    assert "Lovelace" not in text
    assert "ada@example.org" not in text
    assert "S3cret-Code" not in text


def test_details_and_code_on_request() -> None:
    redactor = ContactRedactor()

    assert (
        redactor.apply(DETAILS, include_contact_details=True, include_authorization_code=True)
        == DETAILS
    )


def test_contacts_are_found_at_any_depth_and_in_lists() -> None:
    data: JsonValue = [{"params": {"owner": OWNER}}, {"owner": "not a contact"}, 3]

    filtered = ContactRedactor().apply(data)

    assert filtered == [
        {"params": {"owner": {"type": "individual", "country": "FR", "details": HIDDEN}}},
        {"owner": "not a contact"},
        3,
    ]


def test_empty_authorization_code_stays_empty() -> None:
    assert ContactRedactor().apply({"authinfo": None}) == {"authinfo": None}
    assert ContactRedactor.summary("x") == "x"
