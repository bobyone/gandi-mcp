# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared runner of the endpoint tools: account, rules, filtering and framing."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.content.disclosure import Disclosure
from gandi_mcp.content.result_filter import ResultFilter
from gandi_mcp.domains.page_request import MAX_PAGE, MAX_PER_PAGE, PageRequest
from gandi_mcp.gandi.exceptions import GandiUnexpectedResponseError
from gandi_mcp.gandi.gandi_client import QueryValue
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.endpoint.endpoint_operation import EndpointOperation
from gandi_mcp.operations.operation import Operation
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
UNCHANGED_NEXT_STEP = "It already existed with these values: nothing was changed."
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
PageParameter = Annotated[int, Field(description="Page number, from 1.", ge=1, le=MAX_PAGE)]
PerPageParameter = Annotated[
    int, Field(description="Items per page, 1 to 100.", ge=1, le=MAX_PER_PAGE)
]


def add_write_tool(
    server: MCPServer,
    function: Callable[..., Awaitable[dict[str, Any]]],
    endpoint: Endpoint,
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
    endpoint: Endpoint,
    title: str,
    description: str,
) -> None:
    """Register a read tool named after its endpoint."""
    server.add_tool(
        function, name=endpoint.name, title=title, description=description, annotations=READ_ONLY
    )


def filtered(filters: Sequence[ResultFilter], data: JsonValue, disclosure: Disclosure) -> JsonValue:
    """Apply the result filters in order."""
    for result_filter in filters:
        data = result_filter.filter(data, disclosure)
    return data


class EndpointToolRunner:
    """Run an endpoint for a tool call and describe its result for the model."""

    def __init__(
        self,
        executor: OperationExecutor,
        accounts: AccountsTools,
        filters: Sequence[ResultFilter],
    ) -> None:
        """``filters`` rewrite every result shown to the model, in order (ADR 10)."""
        self._executor = executor
        self._accounts = accounts
        self._filters = tuple(filters)

    async def read(
        self,
        ctx: Context[Any, Any],
        endpoint: Endpoint,
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
            return await self._read(
                ctx,
                operation,
                account,
                request,
                Disclosure(include_contact_details, include_authorization_code),
                adapt,
                when_completed,
            )

        return await self._accounts.guard(run)

    async def read_operation(
        self,
        ctx: Context[Any, Any],
        operation: Callable[[], Operation],
        account: str | None,
    ) -> dict[str, Any]:
        """Read through an operation that is not a single endpoint (several calls).

        The operation is built by a function, so that its validation errors are
        explained like the others.
        """

        async def run() -> dict[str, Any]:
            return await self._read(ctx, operation(), account, None, Disclosure(), None, None)

        return await self._accounts.guard(run)

    async def write_operation(
        self,
        ctx: Context[Any, Any],
        operation: Callable[[], Awaitable[Operation]],
        account: str | None,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        """Change something through an operation that is not a single endpoint call.

        The operation is built by an async function (it may read a file first), so
        that its validation errors are explained like the others.
        """

        async def run() -> dict[str, Any]:
            outcome = await self._executor.run(
                await operation(),
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                confirmation_id,
            )
            if isinstance(outcome, ConfirmationDecision):
                return pending(outcome)
            framed = present(outcome, filtered(self._filters, outcome.data, Disclosure()))
            framed["status"] = "done"
            return framed

        return await self._accounts.guard(run)

    async def _read(  # noqa: PLR0917 - private helper of the two read entry points
        self,
        ctx: Context[Any, Any],
        operation: Operation,
        account: str | None,
        request: PageRequest | None,
        disclosure: Disclosure,
        adapt: Callable[[JsonValue], JsonValue] | None,
        when_completed: str | None,
    ) -> dict[str, Any]:
        result = await self._executor.run(
            operation,
            AccountName(account) if account is not None else None,
            self._accounts.context(ctx),
        )
        if not isinstance(result, UntrustedResult):  # pragma: no cover - reads are never confirmed
            raise TypeError("a read operation cannot wait for a confirmation")
        if result.completed:
            if when_completed is None:
                raise GandiUnexpectedResponseError(f"{operation.name}: unexpected redirect")
            return {"status": "completed", "next_step": when_completed}
        data = adapt(result.data) if adapt else result.data
        return present(result, filtered(self._filters, data, disclosure), request)

    async def write(
        self,
        ctx: Context[Any, Any],
        endpoint: Endpoint,
        account: str | None,
        path_values: Callable[[], Mapping[str, str]],
        *,
        body: Callable[[], JsonValue] | None = None,
        query: Callable[[], Mapping[str, QueryValue | None]] | None = None,
        description_params: Callable[[], Mapping[str, object]] | None = None,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        """Change something through ``endpoint``; confirmed when its category says so.

        Path values, query, body and the parameters of the confirmation description
        (the path values by default) are given as functions, so that their validation
        errors are explained like the others.
        """

        async def run() -> dict[str, Any]:
            values = path_values()
            operation = EndpointOperation(
                endpoint,
                values,
                query() if query else None,
                body() if body else None,
                description_params() if description_params else values,
            )
            outcome = await self._executor.run(
                operation,
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                confirmation_id,
            )
            if isinstance(outcome, ConfirmationDecision):
                return pending(outcome)
            data = filtered(self._filters, outcome.data, Disclosure())
            framed = present(outcome, data)
            if outcome.status == endpoint.unchanged_status:
                framed["status"] = "unchanged"
                framed["next_step"] = UNCHANGED_NEXT_STEP
                return framed
            framed["status"] = "done"
            if endpoint.follow_up is not None:
                framed["next_step"] = f"Follow the operation with {endpoint.follow_up}."
            return framed

        return await self._accounts.guard(run)
