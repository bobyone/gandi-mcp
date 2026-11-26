# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Minimize the personal data and secrets of Gandi domain data sent to the model."""

from gandi_mcp.gandi.gandi_response import JsonValue

# Fields that only a person's contact information has: a mapping carrying one of them
# is a contact, whatever its key (``owner``, ``contacts``, ``holders``...). The names
# come from the domain contacts and from the trademark claim contacts of the Domain API.
# An email alone does not make a contact (it is hidden as a text field, see below);
# a name next to an email does.
PERSONAL_FIELDS = frozenset(
    {
        "streetaddr",
        "street",
        "given",
        "family",
        "phone",
        "mobile",
        "fax",
        "city",
        "zip",
        "pc",
    }
)
# Keys whose mapping is always a domain contact.
CONTACT_ROLES = frozenset({"owner", "admin", "bill", "tech"})
# Keys whose list items are always contacts (trademark claims).
CONTACT_LISTS = frozenset({"contacts", "holders"})
# What a contact summary keeps: its kind and country (``cc`` in trademark claims).
SUMMARY_FIELDS = ("type", "country", "cc", "same_as_owner")
AUTHORIZATION_CODE_FIELD = "authinfo"
EMAIL_SUFFIX = "email"
# Text fields holding a person's name outside a contact (domain lists).
PERSONAL_TEXT_FIELDS = frozenset({"domain_owner"})
HIDDEN = "hidden"


def _is_contact(value: JsonValue) -> bool:
    """A mapping with personal fields, or naming someone next to an email."""
    if not isinstance(value, dict):
        return False
    return not PERSONAL_FIELDS.isdisjoint(value) or {"name", "email"} <= value.keys()


def _is_personal_text(key: str) -> bool:
    """``email``, ``new_owner_email``, ``old_admin_email``, ``domain_owner``..."""
    lowered = key.lower()
    return lowered.endswith(EMAIL_SUFFIX) or lowered in PERSONAL_TEXT_FIELDS


class ContactRedactor:
    """Keep only the type and country of each contact, unless details are wanted.

    At any depth of the data, a mapping under a contact role (``owner``, ``admin``,
    ``bill``, ``tech``), in a ``contacts`` or ``holders`` list, or carrying personal
    fields is a contact and is summarized,
    and a text value whose field name ends with ``email`` (owner change parameters,
    form of authorization answers) or names the owner (``domain_owner``) is hidden.
    The authorization code of a domain, which allows a transfer, is hidden unless
    explicitly requested.
    """

    def apply(
        self,
        data: JsonValue,
        *,
        include_contact_details: bool = False,
        include_authorization_code: bool = False,
    ) -> JsonValue:
        """Return a filtered copy of Gandi data, at any depth."""
        if isinstance(data, list):
            return [
                self.apply(
                    item,
                    include_contact_details=include_contact_details,
                    include_authorization_code=include_authorization_code,
                )
                for item in data
            ]
        if not isinstance(data, dict):
            return data
        if _is_contact(data) and not include_contact_details:
            return self.summary(data)
        filtered: dict[str, JsonValue] = {}
        for key, value in data.items():
            if key == AUTHORIZATION_CODE_FIELD and not include_authorization_code:
                filtered[key] = HIDDEN if value else value
            elif key in CONTACT_ROLES and isinstance(value, dict) and not include_contact_details:
                filtered[key] = self.summary(value)
            elif key in CONTACT_LISTS and isinstance(value, list) and not include_contact_details:
                filtered[key] = [self.summary(item) for item in value]
            elif _is_personal_text(key) and isinstance(value, str) and not include_contact_details:
                filtered[key] = HIDDEN if value else value
            else:
                filtered[key] = self.apply(
                    value,
                    include_contact_details=include_contact_details,
                    include_authorization_code=include_authorization_code,
                )
        return filtered

    @staticmethod
    def summary(contact: JsonValue) -> JsonValue:
        """The role-independent summary of one contact."""
        if not isinstance(contact, dict):
            return contact
        kept: dict[str, JsonValue] = {
            field: contact[field] for field in SUMMARY_FIELDS if field in contact
        }
        kept["details"] = HIDDEN
        return kept
