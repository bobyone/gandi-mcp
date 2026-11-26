# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Token verification with the Gandi ``organization/user-info`` endpoint."""

from gandi_mcp.accounts.account_identity import AccountIdentity
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import TokenRejectedError
from gandi_mcp.accounts.token_verifier import TokenVerifier
from gandi_mcp.gandi.exceptions import (
    GandiAuthenticationError,
    GandiPermissionError,
    GandiUnexpectedResponseError,
)
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

USER_INFO_PATH = ("organization", "user-info")
MAX_FIELD_LENGTH = 200


def _bounded(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()[:MAX_FIELD_LENGTH]


class GandiTokenVerifier(TokenVerifier):
    """Ask Gandi who the token belongs to; a refusal means the token is rejected."""

    def __init__(self, client: GandiClient) -> None:
        self._client = client

    async def verify(self, environment: Environment, token: PersonalAccessToken) -> AccountIdentity:
        try:
            response = await self._client.request(environment, token, "GET", USER_INFO_PATH)
        except (GandiAuthenticationError, GandiPermissionError) as error:
            raise TokenRejectedError(
                f"Gandi refused the token in the {environment.value} environment"
            ) from error
        data = response.data
        username = _bounded(data.get("username")) if isinstance(data, dict) else None
        if not isinstance(data, dict) or username is None:
            raise GandiUnexpectedResponseError("Gandi returned no user name for the token")
        return AccountIdentity(username, _bounded(data.get("name")))
