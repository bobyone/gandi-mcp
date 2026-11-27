# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tool parameter of a domain contact, turned into a validated ``DomainContact``."""

from typing import Literal

from pydantic import BaseModel, Field

from gandi_mcp.domains.contacts.domain_contact import (
    MAX_EMAIL_LENGTH,
    MAX_FIELD_LENGTH,
    ContactType,
    DomainContact,
)

Text = Field(min_length=1, max_length=MAX_FIELD_LENGTH)


class ContactParameter(BaseModel):
    """A domain contact as the user gives it. Only ask the user for these fields."""

    type: Literal["individual", "company", "association", "publicbody"] = Field(
        description="Kind of contact."
    )
    given: str = Field(description="First name.", min_length=1, max_length=MAX_FIELD_LENGTH)
    family: str = Field(description="Last name.", min_length=1, max_length=MAX_FIELD_LENGTH)
    email: str = Field(description="Email address.", min_length=3, max_length=MAX_EMAIL_LENGTH)
    streetaddr: str = Field(
        description="Street address.", min_length=1, max_length=MAX_FIELD_LENGTH
    )
    city: str = Field(description="City.", min_length=1, max_length=MAX_FIELD_LENGTH)
    zip: str = Field(description="Postal code.", min_length=1, max_length=MAX_FIELD_LENGTH)
    country: str = Field(description="ISO 3166 country code, e.g. FR.", min_length=2, max_length=2)
    phone: str | None = Field(
        default=None, description="Phone, written +33.123456789.", max_length=20
    )
    orgname: str | None = Field(
        default=None,
        description="Legal name of the organization; required unless individual.",
        max_length=MAX_FIELD_LENGTH,
    )
    state: str | None = Field(default=None, description="State code, e.g. FR-IDF.", max_length=20)

    def to_contact(self) -> DomainContact:
        """Validate the contact.

        Raises:
            InvalidContactError: if a field is missing or badly formed.
        """
        return DomainContact(
            type=ContactType(self.type),
            given=self.given,
            family=self.family,
            email=self.email,
            streetaddr=self.streetaddr,
            city=self.city,
            zip=self.zip,
            country=self.country,
            phone=self.phone,
            orgname=self.orgname,
            state=self.state,
        )
