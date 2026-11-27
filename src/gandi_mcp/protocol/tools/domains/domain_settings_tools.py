# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools changing the settings of a domain, or deleting it."""

from collections.abc import Callable
from typing import Annotated, Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from pydantic import Field

from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.domains.domain_name import DomainName
from gandi_mcp.gandi.gandi_response import JsonValue
from gandi_mcp.operations.domain import domain_endpoints
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.domains.domain_parameters import DomainParameter
from gandi_mcp.protocol.tools.endpoint_tool_runner import (
    AccountParameter,
    ConfirmationIdParameter,
    EndpointToolRunner,
    add_write_tool,
)

MAX_AUTORENEW_YEARS = 9


class DomainSettingsTools(ToolModule):
    """Automatic renewal, transfer lock, authorization code, reachability, claims, deletion."""

    def __init__(self, runner: EndpointToolRunner) -> None:
        self._runner = runner

    def register(self, server: MCPServer) -> None:
        tools = (
            (
                self.domain_autorenew_update,
                domain_endpoints.AUTORENEW,
                "Turn the automatic renewal of a domain on or off",
                "Turn the automatic renewal of a domain on or off; when on, Gandi renews it "
                "before it expires and charges the paying organization.",
            ),
            (
                self.domain_transfer_lock,
                domain_endpoints.TRANSFER_LOCK,
                "Lock the transfer of a domain",
                "Lock a domain against transfers to another registrar.",
            ),
            (
                self.domain_transfer_unlock,
                domain_endpoints.TRANSFER_UNLOCK,
                "Unlock the transfer of a domain",
                "Unlock a domain so that it can be transferred to another registrar.",
            ),
            (
                self.domain_authorization_code_reset,
                domain_endpoints.AUTHORIZATION_CODE_RESET,
                "Reset the authorization code of a domain",
                "Generate a new authorization code for a domain; the previous one stops "
                "working. It is not returned: read it with domain_details if the user asks.",
            ),
            (
                self.domain_reachability_resend,
                domain_endpoints.REACHABILITY_RESEND,
                "Resend the contact verification email",
                "Resend the email asking the owner to verify their contact details.",
            ),
            (
                self.domain_claims_accept,
                domain_endpoints.CLAIMS_ACCEPT,
                "Accept the trademark claims of a domain",
                "Accept the trademark claims notified for a domain being registered. Only "
                "after the user read them (domain_claims) and explicitly accepted them.",
            ),
            (
                self.domain_delete,
                domain_endpoints.DELETE,
                "Delete a domain",
                "Delete a domain: it is lost for good.",
            ),
        )
        for function, endpoint, title, description in tools:
            add_write_tool(server, function, endpoint, title, description)

    async def domain_autorenew_update(
        self,
        domain: DomainParameter,
        enabled: Annotated[bool, Field(description="Turn the automatic renewal on or off.")],
        ctx: Context[Any, Any],
        *,
        duration: Annotated[
            int | None,
            Field(default=None, description="Years renewed each time.", ge=1, le=9),
        ] = None,
        organization_id: Annotated[
            str | None,
            Field(default=None, description="Organization paying the renewals.", max_length=36),
        ] = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Turn the automatic renewal on or off."""

        def body() -> JsonValue:
            fields: dict[str, JsonValue] = {"enabled": enabled}
            if duration is not None:
                fields["duration"] = duration
            if organization_id is not None:
                fields["org_id"] = str(OrganizationId(organization_id))
            return fields

        return await self._write(ctx, domain_endpoints.AUTORENEW, domain, account, body)

    async def domain_transfer_lock(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Lock the transfer."""
        return await self._write(
            ctx,
            domain_endpoints.TRANSFER_LOCK,
            domain,
            account,
            lambda: {"clientTransferProhibited": True},
        )

    async def domain_transfer_unlock(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Unlock the transfer, after confirmation."""
        return await self._write(
            ctx,
            domain_endpoints.TRANSFER_UNLOCK,
            domain,
            account,
            lambda: {"clientTransferProhibited": False},
            confirmation_id=confirmation_id,
        )

    async def domain_authorization_code_reset(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Reset the authorization code, after confirmation."""
        return await self._write(
            ctx,
            domain_endpoints.AUTHORIZATION_CODE_RESET,
            domain,
            account,
            confirmation_id=confirmation_id,
        )

    async def domain_reachability_resend(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Resend the verification email."""
        return await self._write(
            ctx,
            domain_endpoints.REACHABILITY_RESEND,
            domain,
            account,
            lambda: {"action": "resend"},
        )

    async def domain_claims_accept(
        self, domain: DomainParameter, ctx: Context[Any, Any], account: AccountParameter = None
    ) -> dict[str, Any]:
        """Accept the trademark claims."""
        return await self._write(ctx, domain_endpoints.CLAIMS_ACCEPT, domain, account)

    async def domain_delete(
        self,
        domain: DomainParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationIdParameter = None,
        account: AccountParameter = None,
    ) -> dict[str, Any]:
        """Delete a domain."""
        return await self._write(
            ctx, domain_endpoints.DELETE, domain, account, confirmation_id=confirmation_id
        )

    async def _write(
        self,
        ctx: Context[Any, Any],
        endpoint: Endpoint,
        domain: str,
        account: str | None,
        body: Callable[[], JsonValue] | None = None,
        *,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        return await self._runner.write(
            ctx,
            endpoint,
            account,
            lambda: {"domain": DomainName(domain).value},
            body=body,
            confirmation_id=confirmation_id,
        )
