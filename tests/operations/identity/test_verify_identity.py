# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the identity operation."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.gandi_response import GandiResponse
from gandi_mcp.operations.identity.verify_identity import DESCRIPTION, VerifyIdentity
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio


async def test_reads_user_info() -> None:
    client = FakeGandiClient([GandiResponse(200, {"username": "ada"})])
    operation = VerifyIdentity()
    token = PersonalAccessToken("pat_0123456789abcdef")

    response = await operation.execute(client, Environment.PRODUCTION, token)

    assert response.data == {"username": "ada"}
    assert client.calls[0].path == ("organization", "user-info")
    assert operation.category is OperationCategory.READ
    assert operation.describe().message == DESCRIPTION
    assert operation.subject() == "organization.user_info:{}"
