# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the organizations listed by the Gandi Organization API."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.gandi.gandi_organization_directory import GandiOrganizationDirectory
from gandi_mcp.accounts.organization import Organization
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

ORG_ID = "5a53edc7-b514-416a-98c2-2d477a288eb9"
OTHER_ID = "0b1c2d3e-4f50-4617-8899-aabbccddeeff"
pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")


async def test_keeps_only_the_identifier_name_and_type() -> None:
    client = FakeGandiClient(
        [
            GandiResponse(
                200,
                [
                    {
                        "id": ORG_ID,
                        "name": "  Ada   Corp ",
                        "type": "company",
                        "email": "ada@example.org",
                        "firstname": "Ada",
                    },
                    {"id": "not-a-uuid", "name": "x"},
                    {"name": "no id"},
                    "garbage",
                    {"id": OTHER_ID, "name": "x" * 500},
                ],
            )
        ]
    )

    found = await GandiOrganizationDirectory(client).organizations(Environment.SANDBOX, TOKEN)

    assert found[0] == Organization(OrganizationId(ORG_ID), "Ada Corp", "company")
    assert len(found) == 2
    assert len(found[1].name) == 100
    assert found[1].type == ""
    call = client.calls[0]
    assert (call.method, call.path, call.query) == (
        "GET",
        ("organization", "organizations"),
        {"per_page": 500},
    )


async def test_refuses_an_unexpected_answer() -> None:
    client = FakeGandiClient([GandiResponse(200, {"not": "a list"})])

    with pytest.raises(GandiUnexpectedResponseError):
        await GandiOrganizationDirectory(client).organizations(Environment.SANDBOX, TOKEN)
