# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of the identifier of a Gandi organization."""

import uuid
from dataclasses import dataclass

from gandi_mcp.accounts.exceptions import InvalidOrganizationIdError


@dataclass(frozen=True)
class OrganizationId:
    """The UUID of a Gandi organization, in its canonical lowercase form."""

    value: str

    def __post_init__(self) -> None:
        try:
            canonical = str(uuid.UUID(self.value.strip()))
        except (ValueError, AttributeError) as error:
            raise InvalidOrganizationIdError("an organization identifier is a UUID") from error
        object.__setattr__(self, "value", canonical)

    def __str__(self) -> str:
        return self.value
