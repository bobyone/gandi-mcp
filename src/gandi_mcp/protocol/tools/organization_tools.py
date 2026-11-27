# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools listing the organizations of an account and choosing the paying one."""

from typing import Annotated, Any

from mcp.server import MCPServer
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.accounts.organization_service import OrganizationService
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools, summary
from gandi_mcp.protocol.untrusted_result_presenter import UNTRUSTED_NOTICE

AccountParameter = Annotated[
    str | None,
    Field(
        default=None, description="Account name; the default account when omitted.", max_length=40
    ),
]


class OrganizationTools(ToolModule):
    """``list_organizations`` and ``set_paying_organization``."""

    def __init__(self, organizations: OrganizationService, accounts: AccountsTools) -> None:
        self._organizations = organizations
        self._accounts = accounts

    def register(self, server: MCPServer) -> None:
        server.add_tool(
            self.list_organizations,
            name="list_organizations",
            title="List the organizations of an account",
            description="List the Gandi organizations the account can use (identifier, name, "
            "type), to choose the one paying the orders.",
            annotations=ToolAnnotations(
                read_only_hint=True, idempotent_hint=True, open_world_hint=True
            ),
        )
        server.add_tool(
            self.set_paying_organization,
            name="set_paying_organization",
            title="Choose the paying organization of an account",
            description="Choose the organization paying the orders of an account by default, "
            "among those listed by list_organizations; omit organization_id to clear it. "
            "Only changes a preference on this computer.",
            annotations=ToolAnnotations(
                read_only_hint=False, idempotent_hint=True, open_world_hint=True
            ),
        )

    async def list_organizations(self, account: AccountParameter = None) -> dict[str, Any]:
        """List the organizations of an account."""

        async def run() -> dict[str, Any]:
            found = await self._organizations.organizations(_name(account))
            return {
                "notice": UNTRUSTED_NOTICE,
                "untrusted_data": [
                    {"id": str(item.id), "name": item.name, "type": item.type} for item in found
                ],
            }

        return await self._accounts.guard(run)

    async def set_paying_organization(
        self,
        account: AccountParameter = None,
        organization_id: Annotated[
            str | None,
            Field(
                default=None,
                description="Identifier returned by list_organizations; omit to clear.",
                max_length=36,
            ),
        ] = None,
    ) -> dict[str, Any]:
        """Choose or clear the paying organization."""

        async def run() -> dict[str, Any]:
            organization = OrganizationId(organization_id) if organization_id else None
            changed = await self._organizations.set_paying_organization(
                _name(account), organization
            )
            return {"account": summary(changed)}

        return await self._accounts.guard(run)


def _name(account: str | None) -> AccountName | None:
    return AccountName(account) if account is not None else None
