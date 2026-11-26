# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the organization identifiers."""

import pytest

from gandi_mcp.accounts.exceptions import InvalidOrganizationIdError
from gandi_mcp.accounts.organization_id import OrganizationId

ORG_ID = "5a53edc7-b514-416a-98c2-2d477a288eb9"
OTHER_ID = "0b1c2d3e-4f50-4617-8899-aabbccddeeff"


def test_canonical_form() -> None:
    assert str(OrganizationId(f" {ORG_ID.upper()} ")) == ORG_ID
    assert OrganizationId(ORG_ID.upper()) == OrganizationId(ORG_ID)


@pytest.mark.parametrize("value", ["", "abc", ORG_ID + "x", "../../etc"])
def test_invalid_identifiers(value: str) -> None:
    with pytest.raises(InvalidOrganizationIdError):
        OrganizationId(value)
