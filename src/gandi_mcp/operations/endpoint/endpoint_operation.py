# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run one declared endpoint with validated arguments (interpreter of the catalogue)."""

from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.gandi.gandi_client import GandiClient, QueryValue
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import Message
from gandi_mcp.operations.endpoint.endpoint import PLACEHOLDER, Endpoint
from gandi_mcp.operations.endpoint.exceptions import InvalidEndpointArgumentsError
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import MAX_SECRET_LENGTH, SecretValue


class EndpointOperation(Operation):
    """An operation built from an :class:`Endpoint` and its arguments.

    Path values must come from validated value objects (``DomainName``,
    ``HostLabel``...); each one fills exactly one path segment.
    """

    def __init__(
        self,
        endpoint: Endpoint,
        path_values: Mapping[str, str],
        query: Mapping[str, QueryValue | None] | None = None,
        body: JsonValue = None,
        description_params: Mapping[str, object] | None = None,
    ) -> None:
        """Check the arguments against the specification.

        Raises:
            InvalidEndpointArgumentsError: if a path value is missing or empty, or a query
                parameter is not accepted by the endpoint.
        """
        if set(path_values) != set(endpoint.placeholders):
            raise InvalidEndpointArgumentsError(f"{endpoint.name}: wrong path arguments")
        if any(not value or "/" in value for value in path_values.values()):
            raise InvalidEndpointArgumentsError(f"{endpoint.name}: invalid path argument")
        given: dict[str, QueryValue] = {
            key: value for key, value in (query or {}).items() if value is not None
        }
        unknown = sorted(set(given) - endpoint.query)
        if unknown:
            raise InvalidEndpointArgumentsError(f"{endpoint.name}: unknown parameters {unknown}")
        self._endpoint = endpoint
        self._path_values = dict(path_values)
        self._query = given
        self._body = body
        self._description_params = dict(description_params or path_values)

    @property
    def endpoint(self) -> Endpoint:
        """The specification this operation runs."""
        return self._endpoint

    @property
    def name(self) -> str:
        return self._endpoint.name

    @property
    def category(self) -> OperationCategory:
        return self._endpoint.category

    def parameters(self) -> Mapping[str, JsonValue]:
        query: dict[str, JsonValue] = {}
        for key, value in self._query.items():
            query[key] = value if isinstance(value, str | int) else [str(item) for item in value]
        return {"path": dict(self._path_values), "query": query, "body": self._body}

    def describe(self) -> LocalizedText:
        message = self._endpoint.description or Message(self._endpoint.name)
        return LocalizedText(message, self._description_params)

    @property
    def authenticated(self) -> bool:
        return self._endpoint.authenticated

    def secret_input(self) -> SecretInput | None:
        label = self._endpoint.secret_label
        return SecretInput(label, MAX_SECRET_LENGTH) if label is not None else None

    def segments(self) -> tuple[str, ...]:
        """The path with its placeholders filled."""
        return tuple(
            self._path_values[match.group(1)] if (match := PLACEHOLDER.match(segment)) else segment
            for segment in self._endpoint.path
        )

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken | None,
        secret: SecretValue | None = None,
    ) -> GandiResponse:
        return await client.request(
            environment,
            token,
            self._endpoint.method,
            self.segments(),
            query=self._query or None,
            body=self._with_secret(secret),
            accept_see_other=self._endpoint.completes_with_see_other,
            accept=self._endpoint.accept,
        )

    async def check(
        self, client: GandiClient, environment: Environment, token: PersonalAccessToken
    ) -> GandiResponse | None:
        if not self._endpoint.supports_dry_run:
            return None
        return await client.request(
            environment,
            token,
            self._endpoint.method,
            self.segments(),
            query=self._query or None,
            body=self._body,
            dry_run=True,
        )

    def _with_secret(self, secret: SecretValue | None) -> JsonValue:
        field = self._endpoint.secret_field
        if field is None or secret is None:
            return self._body
        body = self._body if isinstance(self._body, dict) else {}
        return {**body, field: secret.reveal()}
