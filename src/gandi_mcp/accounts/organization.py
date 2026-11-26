# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a Gandi organization the user belongs to."""

from dataclasses import dataclass

from gandi_mcp.accounts.organization_id import OrganizationId


@dataclass(frozen=True)
class Organization:
    """An organization that can pay for orders (the ``sharing_id`` of Gandi).

    Attributes:
        id: Identifier of the organization.
        name: Name given by Gandi (untrusted, bounded).
        type: Kind of organization, such as ``individual`` or ``company``.
    """

    id: OrganizationId
    name: str
    type: str
