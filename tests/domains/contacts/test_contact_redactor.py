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


def test_owner_change_and_authorization_emails_are_hidden() -> None:
    # Documented shapes of GET /domain/changeowner/{domain} and /domain/transferin/{domain}.
    status: JsonValue = {
        "step": "WAIT",
        "params": {
            "answer_new_owner": "T",
            "new_owner_email": "alice@example.org",
            "old_owner_email": "john@doe.com",
            "old_admin_email": "",
        },
        "foa": [{"answer": "T", "email": "admin@example.org", "inner_step": "waiting"}],
    }

    filtered = ContactRedactor().apply(status)

    assert filtered == {
        "step": "WAIT",
        "params": {
            "answer_new_owner": "T",
            "new_owner_email": HIDDEN,
            "old_owner_email": HIDDEN,
            "old_admin_email": "",
        },
        "foa": [{"answer": "T", "email": HIDDEN, "inner_step": "waiting"}],
    }
    assert ContactRedactor().apply(status, include_contact_details=True) == status


def test_trademark_claim_contacts_and_holders_are_summarized() -> None:
    # Documented shape of GET /domain/domains/{domain}/claims.
    person: JsonValue = {
        "name": "Ada Lovelace",
        "org": "Example Ltd",
        "email": "ada@example.org",
        "street": "1 rue de Paris",
        "city": "Paris",
        "pc": "75001",
        "cc": "FR",
        "phone": "+33.123456789",
    }
    claims: JsonValue = {
        "claims": [{"mark_name": "Example", "contacts": [person], "holders": [person]}]
    }

    filtered = ContactRedactor().apply(claims)

    summary = {"cc": "FR", "details": HIDDEN}
    assert filtered == {
        "claims": [{"mark_name": "Example", "contacts": [summary], "holders": [summary]}]
    }


def test_claim_entries_are_contacts_by_position() -> None:
    # Every field of a claim contact or holder is optional: a name alone is personal.
    claims: JsonValue = {
        "claims": [{"contacts": [{"name": "Ada Lovelace", "cc": "FR"}], "holders": [{"org": "X"}]}]
    }

    assert ContactRedactor().apply(claims) == {
        "claims": [
            {
                "contacts": [{"cc": "FR", "details": HIDDEN}],
                "holders": [{"details": HIDDEN}],
            }
        ]
    }
    assert ContactRedactor().apply(claims, include_contact_details=True) == claims


def test_owner_names_of_domain_lists_are_hidden() -> None:
    listing: JsonValue = [{"fqdn": "example.net", "owner": "alice_doe", "domain_owner": "Alice"}]

    assert ContactRedactor().apply(listing) == [
        {"fqdn": "example.net", "owner": "alice_doe", "domain_owner": HIDDEN}
    ]
