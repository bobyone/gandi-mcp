# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the endpoint specifications and their interpreter."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.gandi.media_type import MediaType
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.endpoint.exceptions import InvalidEndpointArgumentsError
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
VALUES = {"domain": "example.com", "host": "ns1", "tld": "fr"}


def test_specifications_are_checked() -> None:
    with pytest.raises(ValueError, match="method"):
        Endpoint("x", "TRACE", ("a",), OperationCategory.READ)
    with pytest.raises(ValueError, match="path"):
        Endpoint("x", "GET", (), OperationCategory.READ)
    with pytest.raises(ValueError, match="description"):
        Endpoint("x", "DELETE", ("a",), OperationCategory.DESTRUCTIVE)
    endpoint = Endpoint(
        "x",
        "DELETE",
        ("a", "{domain}", "b", "{host}"),
        OperationCategory.DESTRUCTIVE,
        description=Message("m"),
    )
    assert endpoint.placeholders == ("domain", "host")


async def test_runs_the_endpoint_with_its_arguments() -> None:
    client = FakeGandiClient()
    operation = EndpointOperation(
        domain_endpoints.LIST_DOMAINS, {}, {"page": 2, "per_page": 10, "tld": None}
    )

    await operation.execute(client, Environment.SANDBOX, TOKEN)

    call = client.calls[0]
    assert (call.method, call.path, call.query) == (
        "GET",
        ("domain", "domains"),
        {"page": 2, "per_page": 10},
    )
    assert operation.parameters() == {
        "path": {},
        "query": {"page": 2, "per_page": 10},
        "body": None,
    }
    assert operation.category is OperationCategory.READ
    assert operation.name == "domain_list"
    assert operation.endpoint is domain_endpoints.LIST_DOMAINS


def test_describes_itself_with_its_values() -> None:
    operation = EndpointOperation(domain_endpoints.DETAILS, {"domain": "example.com"})

    text = operation.describe()

    assert text.params == {"domain": "example.com"}


@pytest.mark.parametrize(
    ("values", "query"),
    [
        ({}, None),
        ({"domain": "example.com", "other": "x"}, None),
        ({"domain": ""}, None),
        ({"domain": "a/b"}, None),
        ({"domain": "example.com"}, {"unexpected": "1"}),
    ],
)
def test_refuses_invalid_arguments(values: dict[str, str], query: dict[str, str] | None) -> None:
    with pytest.raises(InvalidEndpointArgumentsError):
        EndpointOperation(domain_endpoints.DETAILS, values, query)


def test_secret_fields_need_their_label() -> None:
    with pytest.raises(ValueError, match="secret"):
        Endpoint(
            "x", "PUT", ("a",), OperationCategory.WRITE, description=Message("m"), secret_field="s"
        )
    with pytest.raises(ValueError, match="description"):
        Endpoint(
            "x", "PUT", ("a",), OperationCategory.WRITE, secret_field="s", secret_label=Message("l")
        )


async def test_dry_run_and_secret_of_an_endpoint() -> None:
    client = FakeGandiClient()
    plain = EndpointOperation(
        domain_endpoints.TAG_ADD, {"domain": "example.com"}, body={"tag": "a"}
    )
    checked = EndpointOperation(
        domain_endpoints.OWNER_CHANGE, {"domain": "example.com"}, body={"owner": {}}
    )
    code = EndpointOperation(domain_endpoints.TRANSFER_IN_CODE_UPDATE, {"domain": "example.com"})

    assert await plain.check(client, Environment.SANDBOX, TOKEN) is None
    await checked.check(client, Environment.SANDBOX, TOKEN)
    await code.execute(client, Environment.SANDBOX, TOKEN, SecretValue("Auth-123"))
    await code.execute(client, Environment.SANDBOX, TOKEN)

    assert client.calls[0].dry_run
    assert client.calls[0].body == {"owner": {}}
    assert client.calls[1].body == {"authinfo": "Auth-123"}
    assert client.calls[2].body is None
    assert plain.secret_input() is None
    assert code.secret_input() is not None
    assert "Auth-123" not in code.subject()


def test_a_public_endpoint_can_only_read() -> None:
    with pytest.raises(ValueError, match="public"):
        Endpoint("x", "POST", ("x",), OperationCategory.WRITE, authenticated=False)


async def test_a_text_endpoint_asks_for_text_and_a_public_one_says_so() -> None:
    client = FakeGandiClient()
    text = Endpoint(
        "zone", "GET", ("zone", "{domain}"), OperationCategory.READ, accept=MediaType.TEXT
    )
    public = Endpoint("ns", "GET", ("ns", "{domain}"), OperationCategory.READ, authenticated=False)

    await EndpointOperation(text, {"domain": "example.com"}).execute(
        client, Environment.SANDBOX, TOKEN
    )

    assert client.calls[0].accept is MediaType.TEXT
    assert EndpointOperation(text, {"domain": "example.com"}).authenticated
    assert not EndpointOperation(public, {"domain": "example.com"}).authenticated
