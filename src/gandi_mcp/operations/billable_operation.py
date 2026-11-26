# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Abstraction of an operation that charges the account (an order)."""

from abc import abstractmethod
from collections.abc import Mapping

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_request import QuoteRequest
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import GandiResponse, JsonValue
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from gandi_mcp.secrets.secret_value import SecretValue


class BillableOperation(Operation):
    """An order: quoted, checked with a dry run if possible, confirmed at its price.

    It only runs through the ``OrderExecutor`` (ADR 7); ``describe()`` must accept a
    ``price`` parameter, filled with the formatted quote.
    """

    @property
    def category(self) -> OperationCategory:
        return OperationCategory.BILLABLE

    @property
    def supports_dry_run(self) -> bool:
        """Whether Gandi accepts the ``Dry-Run`` header for this order."""
        return False

    @property
    def follow_up(self) -> str | None:
        """Name of the tool following the resulting asynchronous operation, if any."""
        return None

    @abstractmethod
    def quote_request(self, paying_organization: OrganizationId | None) -> QuoteRequest:
        """What to price for this order."""

    @abstractmethod
    def order_body(self, quote: Quote) -> JsonValue:
        """The JSON body of the order, given its accepted quote."""

    @property
    @abstractmethod
    def order_path(self) -> tuple[str, ...]:
        """Path segments of the order request (``POST``)."""

    def parameters(self) -> Mapping[str, JsonValue]:
        return {"path": list(self.order_path)}

    async def order(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        quote: Quote,
        *,
        dry_run: bool = False,
        secret: SecretValue | None = None,
    ) -> GandiResponse:
        """Send the order (or check it, with ``dry_run``) at the quoted price.

        Raises:
            GandiError: if Gandi refuses or cannot be reached.
        """
        organization = quote.request.paying_organization
        return await client.request(
            environment,
            token,
            "POST",
            self.order_path,
            query={"sharing_id": str(organization)} if organization is not None else None,
            body=self.with_secret(self.order_body(quote), secret),
            dry_run=dry_run,
        )

    def with_secret(self, body: JsonValue, secret: SecretValue | None) -> JsonValue:
        """Add the secret typed by the user to the body; nothing by default."""
        return body

    async def execute(
        self,
        client: GandiClient,
        environment: Environment,
        token: PersonalAccessToken,
        secret: SecretValue | None = None,
    ) -> GandiResponse:
        raise TypeError("a billable operation only runs through the OrderExecutor")
