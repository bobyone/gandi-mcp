# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Gandi client over HTTPS, with ``httpx2``."""

import json
import logging
import time
from collections.abc import Mapping, Sequence
from urllib.parse import quote

import httpx2

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.exceptions import GandiUnavailableError, GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import GandiClient, QueryValue
from gandi_mcp.gandi.gandi_response import SEE_OTHER, GandiResponse, JsonValue
from gandi_mcp.gandi.http.gandi_error_translator import translate_error
from gandi_mcp.gandi.media_type import MediaType
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
FORBIDDEN_SEGMENTS = frozenset({"", ".", ".."})

logger = logging.getLogger(__name__)


def encode_path(path: Sequence[str]) -> str:
    """Join path segments, encoding each one so that it stays a single segment.

    Raises:
        ValueError: if the path is empty or a segment is empty, ``.`` or ``..``.
    """
    if not path or any(segment in FORBIDDEN_SEGMENTS for segment in path):
        raise ValueError("invalid Gandi API path")
    return "/".join(quote(segment, safe="") for segment in path)


def _decode(response: httpx2.Response, accept: MediaType = MediaType.JSON) -> JsonValue:
    if not response.content:
        return None
    if accept is MediaType.TEXT and response.is_success:
        try:
            return response.content.decode("utf-8")
        except UnicodeDecodeError:
            raise GandiUnexpectedResponseError("Gandi returned an unreadable text") from None
    try:
        decoded: JsonValue = json.loads(response.content)
    except (json.JSONDecodeError, UnicodeDecodeError):
        if response.is_success:
            raise GandiUnexpectedResponseError("Gandi returned an unreadable body") from None
        return None
    return decoded


def _count(value: str | None) -> int | None:
    return int(value) if value is not None and value.strip().isdigit() else None


class HttpGandiClient(GandiClient):
    """Call the Gandi API v5 with a Bearer token.

    One connection pool is reused for every request. Redirects are not followed, so
    that the token is only ever sent to the configured base URLs.
    """

    def __init__(
        self,
        base_urls: Mapping[Environment, str],
        timeout_seconds: float,
        user_agent: str,
        transport: httpx2.AsyncBaseTransport | None = None,
    ) -> None:
        """Configure the client.

        Args:
            base_urls: Base URL of each environment, ending with ``/``.
            timeout_seconds: Timeout of each request.
            user_agent: ``User-Agent`` header sent to Gandi.
            transport: Transport replacing the network, for tests.
        """
        missing = set(Environment) - set(base_urls)
        if missing:
            raise ValueError(f"missing base URL for {', '.join(sorted(missing))}")
        self._base_urls = dict(base_urls)
        self._client = httpx2.AsyncClient(
            timeout=timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": user_agent, "Accept": "application/json"},
            transport=transport,
        )

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
        dry_run: bool = False,
        accept: MediaType = MediaType.JSON,
    ) -> GandiResponse:
        verb = method.upper()
        if verb not in METHODS:
            raise ValueError(f"unsupported HTTP method {method!r}")
        url = self._base_urls[environment] + encode_path(path)
        params = {
            key: (str(value).lower() if isinstance(value, bool) else value)
            for key, value in (query or {}).items()
        }
        headers = {"Accept": accept.value, "Authorization": f"Bearer {token.reveal()}"}
        if dry_run:
            headers["Dry-Run"] = "1"
        started = time.monotonic()
        try:
            response = await self._client.request(
                verb,
                url,
                params=params,
                json=body,
                headers=headers,
            )
        except httpx2.TimeoutException as error:
            raise GandiUnavailableError("Gandi did not answer in time") from error
        except httpx2.HTTPError as error:
            raise GandiUnavailableError("Gandi cannot be reached") from error
        logger.debug(
            "gandi %s %s -> %d in %.0f ms",
            verb,
            environment.value,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
        data = _decode(response, accept)
        # 303 marks a completed operation, only where the caller expects it; it is
        # never followed.
        see_other = accept_see_other and response.status_code == SEE_OTHER
        if not response.is_success and not see_other:
            raise translate_error(response.status_code, data, response.headers)
        return GandiResponse(
            status=response.status_code,
            data=data,
            total_count=_count(response.headers.get("total-count")),
            filtered_count=_count(response.headers.get("filtered-count")),
            location=response.headers.get("location"),
        )

    async def close(self) -> None:
        await self._client.aclose()
