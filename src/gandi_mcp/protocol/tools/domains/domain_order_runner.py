# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Shared runner of the order tools: account, order rules, framing."""

from collections.abc import Callable
from typing import Annotated, Any

from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.content.long_text_filter import LongTextFilter
from gandi_mcp.domains.contacts.contact_redactor import ContactRedactor
from gandi_mcp.domains.registration_duration import MAX_YEARS, MIN_YEARS
from gandi_mcp.operations.billable_operation import BillableOperation
from gandi_mcp.operations.order_executor import OrderExecutor
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools, pending
from gandi_mcp.protocol.untrusted_result_presenter import present

BILLABLE = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=True
)

PayingOrganizationParameter = Annotated[
    str | None,
    Field(
        default=None,
        description="Organization paying this order (from list_organizations); the "
        "account's paying organization when omitted.",
        max_length=36,
    ),
]
DurationParameter = Annotated[
    int, Field(description="Duration in years.", ge=MIN_YEARS, le=MAX_YEARS)
]


class DomainOrderRunner:
    """Run an order for a tool call and describe its outcome for the model."""

    def __init__(
        self,
        orders: OrderExecutor,
        accounts: AccountsTools,
        redactor: ContactRedactor,
        long_texts: LongTextFilter,
    ) -> None:
        self._orders = orders
        self._accounts = accounts
        self._redactor = redactor
        self._long_texts = long_texts

    async def order(
        self,
        ctx: Context[Any, Any],
        operation: Callable[[], BillableOperation],
        account: str | None,
        confirmation_id: str | None,
        paying_organization: str | None,
    ) -> dict[str, Any]:
        """Order through the ``OrderExecutor``; errors become explained tool errors.

        ``operation`` builds the validated operation, so that its validation errors
        are explained like the others.
        """

        async def run() -> dict[str, Any]:
            built = operation()
            organization = OrganizationId(paying_organization) if paying_organization else None
            outcome = await self._orders.run(
                built,
                AccountName(account) if account is not None else None,
                self._accounts.context(ctx),
                confirmation_id,
                organization,
            )
            if isinstance(outcome, ConfirmationDecision):
                return pending(outcome)
            data = self._long_texts.apply(self._redactor.apply(outcome.data))
            framed = present(outcome, data)
            framed["status"] = "ordered"
            if built.follow_up is not None:
                framed["next_step"] = f"Follow the operation with {built.follow_up}."
            return framed

        return await self._accounts.guard(run)
