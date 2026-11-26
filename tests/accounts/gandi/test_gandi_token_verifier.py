# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the Gandi token verifier, with a fake Gandi client."""

import pytest

from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import TokenRejectedError
from gandi_mcp.accounts.gandi.gandi_token_verifier import MAX_FIELD_LENGTH, GandiTokenVerifier
from gandi_mcp.gandi.exceptions import (
    GandiAuthenticationError,
    GandiPermissionError,
    GandiUnavailableError,
    GandiUnexpectedResponseError,
)
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")


async def test_returns_the_identity_from_user_info() -> None:
    client = FakeGandiClient(
        [GandiResponse(200, {"username": "ada", "name": "Ada", "email": "a@example.org"})]
    )

    identity = await GandiTokenVerifier(client).verify(Environment.SANDBOX, TOKEN)

    assert identity == AccountIdentity("ada", "Ada")
    call = client.calls[0]
    assert (call.environment, call.method, call.path) == (
        Environment.SANDBOX,
        "GET",
        ("organization", "user-info"),
    )
    assert call.token == TOKEN


async def test_only_a_200_answer_verifies_the_token() -> None:
    client = FakeGandiClient([GandiResponse(303, {"username": "mallory"})])

    with pytest.raises(GandiUnexpectedResponseError):
        await GandiTokenVerifier(client).verify(Environment.SANDBOX, TOKEN)

    assert not client.calls[0].accept_see_other


async def test_bounds_and_cleans_the_fields() -> None:
    client = FakeGandiClient([GandiResponse(200, {"username": " " + "u" * 500, "name": " "})])

    identity = await GandiTokenVerifier(client).verify(Environment.SANDBOX, TOKEN)

    assert identity.username == "u" * MAX_FIELD_LENGTH
    assert identity.name is None


@pytest.mark.parametrize("failure", [GandiAuthenticationError("401"), GandiPermissionError("403")])
async def test_refusal_means_rejected(failure: Exception) -> None:
    client = FakeGandiClient([failure])

    with pytest.raises(TokenRejectedError, match="production"):
        await GandiTokenVerifier(client).verify(Environment.PRODUCTION, TOKEN)


async def test_other_errors_pass_through() -> None:
    with pytest.raises(GandiUnavailableError):
        await GandiTokenVerifier(FakeGandiClient([GandiUnavailableError("down")])).verify(
            Environment.SANDBOX, TOKEN
        )


@pytest.mark.parametrize("data", [None, [], {"name": "Ada"}, {"username": 3}])
async def test_unexpected_answers(data: JsonValue) -> None:
    with pytest.raises(GandiUnexpectedResponseError):
        await GandiTokenVerifier(FakeGandiClient([GandiResponse(200, data)])).verify(
            Environment.SANDBOX, TOKEN
        )
