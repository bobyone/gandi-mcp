# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the HTTP Gandi client, with a mock transport."""

import json
from collections.abc import Callable

import httpx2
import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.exceptions import (
    GandiAuthenticationError,
    GandiUnavailableError,
    GandiUnexpectedResponseError,
    GandiValidationError,
)
from gandi_mcp.gandi.http.http_gandi_client import HttpGandiClient, encode_path
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
BASE_URLS = {
    Environment.PRODUCTION: "https://api.gandi.net/v5/",
    Environment.SANDBOX: "https://api.sandbox.gandi.net/v5/",
}


def client_with(handler: Callable[[httpx2.Request], httpx2.Response]) -> HttpGandiClient:
    return HttpGandiClient(BASE_URLS, 5, "gandi-mcp/test", httpx2.MockTransport(handler))


async def test_sends_an_authenticated_request() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=[{"fqdn": "example.com"}], headers={"Total-Count": "41"})

    client = client_with(handler)
    response = await client.request(
        Environment.SANDBOX,
        TOKEN,
        "get",
        ("domain", "domains"),
        query={"per_page": 10, "nameserver": ["a", "b"], "exact": True},
    )
    await client.close()

    request = seen[0]
    assert request.method == "GET"
    assert request.url.host == "api.sandbox.gandi.net"
    assert request.url.path == "/v5/domain/domains"
    assert request.url.params.get_list("nameserver") == ["a", "b"]
    assert request.url.params["exact"] == "true"
    assert request.headers["Authorization"] == f"Bearer {TOKEN.reveal()}"
    assert request.headers["User-Agent"] == "gandi-mcp/test"
    assert response.status == 200
    assert response.data == [{"fqdn": "example.com"}]
    assert response.total_count == 41


async def test_sends_a_json_body_and_reads_the_location() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert json.loads(request.content) == {"fqdn": "example.com"}
        return httpx2.Response(201, headers={"Location": "https://api.gandi.net/v5/x"})

    response = await client_with(handler).request(
        Environment.PRODUCTION, TOKEN, "POST", ("domain", "domains"), body={"fqdn": "example.com"}
    )

    assert response.status == 201
    assert response.data is None
    assert response.location == "https://api.gandi.net/v5/x"
    assert response.total_count is None


async def test_encodes_user_input_in_path_segments() -> None:
    seen: list[str] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request.url.raw_path.decode())
        return httpx2.Response(204)

    await client_with(handler).request(
        Environment.SANDBOX, TOKEN, "DELETE", ("domain", "a/../b?x=1#y")
    )

    assert seen == ["/v5/domain/a%2F..%2Fb%3Fx%3D1%23y"]


@pytest.mark.parametrize("path", [(), ("",), ("domain", ".."), (".",)])
def test_rejects_unsafe_paths(path: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="path"):
        encode_path(path)


async def test_rejects_unknown_methods() -> None:
    with pytest.raises(ValueError, match="method"):
        await client_with(lambda _r: httpx2.Response(200)).request(
            Environment.SANDBOX, TOKEN, "TRACE", ("x",)
        )


def test_needs_every_base_url() -> None:
    with pytest.raises(ValueError, match="sandbox"):
        HttpGandiClient({Environment.PRODUCTION: "https://x/"}, 5, "ua")


async def test_translates_errors_with_details() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(400, json={"message": "bad fqdn"})

    with pytest.raises(GandiValidationError) as raised:
        await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))

    assert raised.value.details == ("bad fqdn",)


async def test_error_with_unreadable_body() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(401, content=b"<html>nope</html>")

    with pytest.raises(GandiAuthenticationError) as raised:
        await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))

    assert raised.value.details == ()
    assert TOKEN.reveal() not in str(raised.value)


async def test_success_with_unreadable_body() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, content=b"\xff not json")

    with pytest.raises(GandiUnexpectedResponseError):
        await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))


async def test_does_not_follow_redirects() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.host == "api.sandbox.gandi.net"
        return httpx2.Response(302, headers={"Location": "https://evil.example/"})

    with pytest.raises(GandiUnexpectedResponseError):
        await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))


async def test_reads_the_matching_count_of_a_filtered_list() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        headers = {"Total-Count": "120", "Filtered-Count": "3"}
        return httpx2.Response(200, json=[], headers=headers)

    response = await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))

    assert (response.total_count, response.filtered_count) == (120, 3)


async def test_see_other_is_returned_without_being_followed() -> None:
    seen: list[httpx2.Request] = []
    location = "https://api.sandbox.gandi.net/v5/domain/domains/example.com"

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(303, headers={"Location": location})

    response = await client_with(handler).request(
        Environment.SANDBOX, TOKEN, "GET", ("x",), accept_see_other=True
    )

    assert len(seen) == 1
    assert (response.status, response.data, response.location) == (303, None, location)


async def test_see_other_is_an_error_unless_expected() -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(303, json={"username": "mallory"}, headers={"Location": "/x"})

    with pytest.raises(GandiUnexpectedResponseError):
        await client_with(handler).request(
            Environment.SANDBOX, TOKEN, "GET", ("organization", "user-info")
        )


@pytest.mark.parametrize(
    ("failure", "message"),
    [
        (httpx2.ConnectTimeout("slow"), "in time"),
        (httpx2.ConnectError("refused"), "reached"),
    ],
)
async def test_network_failures(failure: Exception, message: str) -> None:
    def handler(_request: httpx2.Request) -> httpx2.Response:
        raise failure

    with pytest.raises(GandiUnavailableError, match=message):
        await client_with(handler).request(Environment.SANDBOX, TOKEN, "GET", ("x",))


async def test_dry_run_header() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json={"status": "success"})

    client = client_with(handler)
    await client.request(Environment.SANDBOX, TOKEN, "POST", ("x",), body={}, dry_run=True)
    await client.request(Environment.SANDBOX, TOKEN, "POST", ("x",), body={})

    assert seen[0].headers["Dry-Run"] == "1"
    assert "Dry-Run" not in seen[1].headers
