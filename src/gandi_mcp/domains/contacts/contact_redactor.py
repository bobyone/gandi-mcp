# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Minimize the personal data and secrets of Gandi domain data sent to the model."""

from gandi_mcp.gandi.gandi_response import JsonValue

CONTACT_ROLES = frozenset({"owner", "admin", "bill", "tech"})
# Fields that only a contact has: a role value carrying one of them is a contact.
PERSONAL_FIELDS = frozenset(
    {"email", "streetaddr", "given", "family", "phone", "mobile", "fax", "city", "zip"}
)
SUMMARY_FIELDS = ("type", "country", "same_as_owner")
AUTHORIZATION_CODE_FIELD = "authinfo"
HIDDEN = "hidden"


def _is_contact(value: JsonValue) -> bool:
    return isinstance(value, dict) and not PERSONAL_FIELDS.isdisjoint(value)


class ContactRedactor:
    """Keep only the role, type and country of each contact, unless details are wanted.

    It also hides the authorization code of a domain, which allows a transfer, unless
    it is explicitly requested.
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
        filtered: dict[str, JsonValue] = {}
        for key, value in data.items():
            if key == AUTHORIZATION_CODE_FIELD and not include_authorization_code:
                filtered[key] = HIDDEN if value else value
            elif key in CONTACT_ROLES and _is_contact(value) and not include_contact_details:
                filtered[key] = self.summary(value)
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
