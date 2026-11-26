# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of the access to the Gandi API v5."""

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

type QueryValue = str | int | bool | Sequence[str]


class GandiClient(ABC):
    """Send authenticated requests to the Gandi API of an environment."""

    @abstractmethod
    async def request(
        self,
        environment: Environment,
        token: PersonalAccessToken,
        method: str,
        path: Sequence[str],
        *,
        query: Mapping[str, QueryValue] | None = None,
        body: JsonValue = None,
        accept_see_other: bool = False,
    ) -> GandiResponse:
        """Send a request and return the successful response.

        Args:
            environment: Gandi environment whose base URL is used.
            token: Personal Access Token authenticating the request.
            method: HTTP method (``GET``, ``POST``, ``PUT``, ``PATCH``, ``DELETE``).
            path: Path segments below the base URL, for example
                ``("domain", "domains", "example.com")``; each segment is encoded, so
                user input can never change the path structure.
            query: Query parameters.
            body: JSON body, or ``None`` for no body.
            accept_see_other: Return a ``303 See Other`` (never followed) as a
                response instead of an error; only for endpoints documenting it.

        Raises:
            GandiError: a subclass describing why the request failed.
        """

    @abstractmethod
    async def close(self) -> None:
        """Release the network resources."""
