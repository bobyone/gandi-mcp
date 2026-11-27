# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The contacts given with a registration or a transfer in."""

from collections.abc import Mapping
from dataclasses import dataclass

from gandi_mcp.domains.contacts.domain_contact import DomainContact
from gandi_mcp.gandi.gandi_response import JsonValue


@dataclass(frozen=True)
class DomainContacts:
    """The owner, and optionally the admin, tech and billing contacts.

    Gandi uses the owner for the contacts left out.
    """

    owner: DomainContact
    admin: DomainContact | None = None
    tech: DomainContact | None = None
    bill: DomainContact | None = None

    def to_json(self) -> Mapping[str, JsonValue]:
        """The contacts by role, as Gandi expects them."""
        roles = {"owner": self.owner, "admin": self.admin, "tech": self.tech, "bill": self.bill}
        return {role: contact.to_json() for role, contact in roles.items() if contact}
