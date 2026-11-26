# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared runner of the domain tools: account, rules, filtering and framing."""

from collections.abc import Awaitable, Callable, Mapping
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.domains.contacts.contact_redactor import ContactRedactor
from gandi_mcp.domains.page_request import MAX_PAGE, MAX_PER_PAGE, PageRequest
from gandi_mcp.gandi.gandi_client import QueryValue
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.operations.domain.endpoint_operation import EndpointOperation
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.untrusted_result_presenter import present

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)

AccountParameter = Annotated[
    str | None,
    Field(
        default=None, description="Account name; the default account when omitted.", max_length=40
    ),
]
DomainParameter = Annotated[
    str, Field(description="Domain name, e.g. example.com (Unicode accepted).", max_length=253)
]
PageParameter = Annotated[int, Field(description="Page number, from 1.", ge=1, le=MAX_PAGE)]
PerPageParameter = Annotated[
    int, Field(description="Items per page, 1 to 100.", ge=1, le=MAX_PER_PAGE)
]
ContactDetailsParameter = Annotated[
    bool,
    Field(
        description="Return the full contact details (names, addresses, emails). Only when "
        "the user asks for them: by default only the type and country of each contact."
    ),
]
AuthorizationCodeParameter = Annotated[
    bool,
    Field(
        description="Return the authorization code needed to transfer the domain to "
        "another registrar. Only when the user asks for it."
    ),
]


def add_read_tool(
    server: MCPServer,
    function: Callable[..., Awaitable[dict[str, Any]]],
    endpoint: DomainEndpoint,
    title: str,
    description: str,
) -> None:
    """Register a read tool named after its endpoint."""
    server.add_tool(
        function, name=endpoint.name, title=title, description=description, annotations=READ_ONLY
    )


class DomainToolRunner:
    """Run a domain endpoint for a tool call and describe its result for the model."""

    def __init__(
        self, executor: OperationExecutor, accounts: AccountsTools, redactor: ContactRedactor
    ) -> None:
        self._executor = executor
        self._accounts = accounts
        self._redactor = redactor

    async def read(
        self,
        ctx: Context[Any, Any],
        endpoint: DomainEndpoint,
        account: str | None,
        path_values: Callable[[], Mapping[str, str]] | None = None,
        *,
        query: Callable[[], Mapping[str, QueryValue | None]] | None = None,
        body: JsonValue = None,
        page: tuple[int, int] | None = None,
        include_contact_details: bool = False,
        include_authorization_code: bool = False,
    ) -> dict[str, Any]:
        """Read through ``endpoint``; errors become explained tool errors.

        Path values and query are given as functions, so that their validation errors
        are explained like the others.
        """

        async def run() -> dict[str, Any]:
            full_query: dict[str, QueryValue | None] = dict(query() if query else {})
            request = PageRequest(*page) if page is not None else None
            if request is not None:
                full_query.update(request.query())
            values = path_values() if path_values else {}
            operation = EndpointOperation(endpoint, values, full_query, body)
            result = await self._executor.run(
                operation,
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
            )
            if not isinstance(
                result, UntrustedResult
            ):  # pragma: no cover - reads are never confirmed
                raise TypeError("a read operation cannot wait for a confirmation")
            data = self._redactor.apply(
                result.data,
                include_contact_details=include_contact_details,
                include_authorization_code=include_authorization_code,
            )
            return present(result, data, request)

        return await self._accounts.guard(run)
