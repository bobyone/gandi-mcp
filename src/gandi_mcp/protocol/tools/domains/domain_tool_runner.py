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
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.content.long_text_filter import LongTextFilter
from gandi_mcp.domains.contacts.contact_redactor import ContactRedactor
from gandi_mcp.domains.page_request import MAX_PAGE, MAX_PER_PAGE, PageRequest
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import QueryValue
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.operations.domain.endpoint_operation import EndpointOperation
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools, pending
from gandi_mcp.protocol.untrusted_result_presenter import present

READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=True)
DESTRUCTIVE = ToolAnnotations(
    read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=True
)
CONFIRMED_RULES = (
    " The user confirms outside the conversation; if the result is "
    "confirmation_pending, call again with the same arguments and the returned "
    "confirmation_id once the user answered."
)
ConfirmationIdParameter = Annotated[
    str | None,
    Field(
        default=None,
        description="Identifier returned by a pending confirmation, once the user has "
        "answered on the page opened in their browser. Never invent one.",
        max_length=64,
    ),
]

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


def add_write_tool(
    server: MCPServer,
    function: Callable[..., Awaitable[dict[str, Any]]],
    endpoint: DomainEndpoint,
    title: str,
    description: str,
) -> None:
    """Register a write tool named after its endpoint, annotated from its category."""
    destructive = endpoint.category.needs_confirmation
    server.add_tool(
        function,
        name=endpoint.name,
        title=title,
        description=description + (CONFIRMED_RULES if endpoint.confirmed else ""),
        annotations=DESTRUCTIVE if destructive else WRITE,
    )


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
        self,
        executor: OperationExecutor,
        accounts: AccountsTools,
        redactor: ContactRedactor,
        long_texts: LongTextFilter,
    ) -> None:
        self._executor = executor
        self._accounts = accounts
        self._redactor = redactor
        self._long_texts = long_texts

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
        adapt: Callable[[JsonValue], JsonValue] | None = None,
        when_completed: str | None = None,
    ) -> dict[str, Any]:
        """Read through ``endpoint``; errors become explained tool errors.

        Path values and query are given as functions, so that their validation errors
        are explained like the others. ``adapt`` rewrites the data of this endpoint
        before it is filtered. ``when_completed`` is the next step given to the model
        when Gandi reports the followed operation as complete; without it, such an
        answer is unexpected.
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
            if result.completed:
                if when_completed is None:
                    raise GandiUnexpectedResponseError(f"{endpoint.name}: unexpected redirect")
                return {"status": "completed", "next_step": when_completed}
            data = adapt(result.data) if adapt else result.data
            data = self._redactor.apply(
                data,
                include_contact_details=include_contact_details,
                include_authorization_code=include_authorization_code,
            )
            return present(result, self._long_texts.apply(data), request)

        return await self._accounts.guard(run)

    async def write(
        self,
        ctx: Context[Any, Any],
        endpoint: DomainEndpoint,
        account: str | None,
        path_values: Callable[[], Mapping[str, str]],
        *,
        body: Callable[[], JsonValue] | None = None,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        """Change something through ``endpoint``; confirmed when its category says so.

        Path values and body are given as functions, so that their validation errors
        are explained like the others.
        """

        async def run() -> dict[str, Any]:
            operation = EndpointOperation(endpoint, path_values(), None, body() if body else None)
            outcome = await self._executor.run(
                operation,
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                confirmation_id,
            )
            if isinstance(outcome, ConfirmationDecision):
                return pending(outcome)
            data = self._long_texts.apply(self._redactor.apply(outcome.data))
            framed = present(outcome, data)
            framed["status"] = "done"
            if endpoint.follow_up is not None:
                framed["next_step"] = f"Follow the operation with {endpoint.follow_up}."
            return framed

        return await self._accounts.guard(run)
