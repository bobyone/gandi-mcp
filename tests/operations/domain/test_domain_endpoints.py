# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the catalogue of the Domain API endpoints."""

import pytest

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.fake_gandi_client import FakeGandiClient

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")
VALUES = {"domain": "example.com", "host": "ns1", "tld": "fr"}


def test_catalogue_names_are_unique_and_read_only() -> None:
    names = [endpoint.name for endpoint in domain_endpoints.READ_ENDPOINTS]

    assert len(names) == len(set(names)) == 22
    assert all(name.startswith("domain_") for name in names)
    assert all(e.category is OperationCategory.READ for e in domain_endpoints.READ_ENDPOINTS)


@pytest.mark.parametrize(
    "endpoint", domain_endpoints.READ_ENDPOINTS, ids=lambda endpoint: endpoint.name
)
async def test_every_read_endpoint_calls_its_path(endpoint: Endpoint) -> None:
    client = FakeGandiClient()
    values = {name: VALUES[name] for name in endpoint.placeholders}

    await EndpointOperation(endpoint, values).execute(client, Environment.PRODUCTION, TOKEN)

    call = client.calls[0]
    assert call.method == endpoint.method
    assert call.path[0] == "domain"
    assert "/" not in "".join(call.path)
    assert all(not segment.startswith("{") for segment in call.path)
    for name, value in values.items():
        assert value in call.path, name


def test_all_endpoint_names_are_unique() -> None:
    endpoints = (*domain_endpoints.READ_ENDPOINTS, *domain_endpoints.WRITE_ENDPOINTS)
    names = [endpoint.name for endpoint in endpoints]

    assert len(names) == len(set(names)) == 57
    assert all(e.category is not OperationCategory.READ for e in domain_endpoints.WRITE_ENDPOINTS)
