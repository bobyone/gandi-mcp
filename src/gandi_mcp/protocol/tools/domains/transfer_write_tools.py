# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools acting on transfers in and out of Gandi."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.domains.write_values import EmailAddress
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    DomainParameter,
    DomainToolRunner,
    add_write_tool,
)


class TransferWriteTools(ToolModule):
    """Answer a transfer out; relaunch, fix the code of or resend emails of a transfer in."""

    def __init__(self, runner: DomainToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_transfer_out_accept,
                domain_endpoints.TRANSFER_OUT_ACCEPT,
                "Accept the transfer of a domain out of Gandi",
                "Accept a pending transfer of a domain to another registrar: it leaves Gandi.",
            ),
            (
                self.domain_transfer_out_decline,
                domain_endpoints.TRANSFER_OUT_DECLINE,
                "Decline the transfer of a domain out of Gandi",
                "Decline a pending transfer of a domain to another registrar.",
            ),
            (
                self.domain_transfer_in_relaunch,
                domain_endpoints.TRANSFER_IN_RELAUNCH,
                "Relaunch a transfer to Gandi",
                "Relaunch a transfer to Gandi that stopped on an error.",
            ),
            (
                self.domain_transfer_in_code_update,
                domain_endpoints.TRANSFER_IN_CODE_UPDATE,
                "Correct the authorization code of a transfer to Gandi",
                "Give a new authorization code to a pending transfer to Gandi. Never ask the "
                "user for the code: they type it on the confirmation page.",
            ),
            (
                self.domain_transfer_in_resend,
                domain_endpoints.TRANSFER_IN_RESEND,
                "Resend the transfer approval email",
                "Resend the email asking the owner to approve a transfer to Gandi.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_transfer_out_accept(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Accept a transfer out."""
        return await self._write(
            ctx,
            domain_endpoints.TRANSFER_OUT_ACCEPT,
            domain,
            account,
            {"accept": True},
            confirmation_id=confirmation_id,
        )

    async def domain_transfer_out_decline(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Decline a transfer out."""
        return await self._write(
            ctx, domain_endpoints.TRANSFER_OUT_DECLINE, domain, account, {"accept": False}
        )

    async def domain_transfer_in_relaunch(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Relaunch a transfer in."""
        return await self._write(ctx, domain_endpoints.TRANSFER_IN_RELAUNCH, domain, account)

    async def domain_transfer_in_code_update(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Give a new authorization code, typed by the user on the confirmation page."""
        return await self._write(
            ctx,
            domain_endpoints.TRANSFER_IN_CODE_UPDATE,
            domain,
            account,
            {},
            confirmation_id=confirmation_id,
        )

    async def domain_transfer_in_resend(
        self,
        domain: DomainParameter,
        email: Annotated[
            str, Field(description="Email address to send the approval email to.", max_length=254)
        ],
        ctx: Context[Any, Any],
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Resend the approval email."""
        return await self._runner.write(
            ctx,
            domain_endpoints.TRANSFER_IN_RESEND,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=lambda: {"email": EmailAddress(email).value},
        )

    async def _write(
        self,
        ctx: Context[Any, Any],
        endpoint: DomainEndpoint,
        domain: str,
        account: str | None,
        body: dict[str, JsonValue] | None = None,
        *,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._runner.write(
            ctx,
            endpoint,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=(lambda: body) if body is not None else None,
            confirmation_id=confirmation_id,
        )
