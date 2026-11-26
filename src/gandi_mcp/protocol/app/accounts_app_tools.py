# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""MCP App tools of the accounts: the only tools that ever receive a token."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from mcp.server.apps import Apps, client_supports_apps
from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.verified_account import VerifiedAccount
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.protocol.app.app_resource import APP_URI, register_app_resource
from gandi_mcp.protocol.app_module import AppModule
from gandi_mcp.protocol.error_presenter import AppOnlyToolError
from gandi_mcp.protocol.tools.accounts_tools import (
    AccountNameParameter,
    AccountsTools,
    EnvironmentParameter,
    summary,
)
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken

APP_ONLY: list[Literal["model", "app"]] = ["app"]
TokenParameter = Annotated[str, Field(description="Personal Access Token typed by the user.")]
ReadOnlyParameter = Annotated[bool, Field(description="Refuse every write operation.")]


def verified(result: VerifiedAccount) -> dict[str, Any]:
    """Describe an account whose token Gandi accepted, for the MCP App only."""
    return {"account": summary(result.account), "username": result.identity.username}


class AccountsAppTools(AppModule):
    """``open_gandi_app`` for the model, and the app-only account tools.

    App-only tools are refused unless the client negotiated the MCP Apps extension:
    a client that does not render the App could list them to its model (ADR 4). The
    App confirms destructive actions in its own dialog before calling them.
    """

    def __init__(
        self,
        accounts: AccountService,
        tools: AccountsTools,
        translator: Translator,
        html: str,
    ) -> None:
        self._accounts = accounts
        self._tools = tools
        self._translator = translator
        self._html = html

    def register(self, apps: Apps) -> None:
        register_app_resource(apps, self._html)
        local = ToolAnnotations(read_only_hint=False, open_world_hint=False)
        remote = ToolAnnotations(read_only_hint=False, open_world_hint=True)
        apps.tool(
            resource_uri=APP_URI,
            visibility=["model", "app"],
            name="open_gandi_app",
            title="Open the Gandi app",
            description="Show the Gandi app, where the user manages the Gandi accounts "
            "(add, rename, replace token, remove) and types tokens safely.",
            annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
        )(self.open_gandi_app)
        bindings: list[tuple[Callable[..., Awaitable[dict[str, Any]]], str, ToolAnnotations]] = [
            (self.app_list_accounts, "List the accounts for the Gandi app.", local),
            (self.app_add_account, "Add an account with a token typed in the app.", remote),
            (self.app_update_account, "Rename, lock, unlock or make an account default.", local),
            (self.app_replace_account_token, "Replace a token typed in the app.", remote),
            (self.app_change_account_environment, "Move an account with a new token.", remote),
            (
                self.app_remove_account,
                "Remove an account confirmed in the app.",
                local.model_copy(update={"destructive_hint": True}),
            ),
        ]
        for function, description, annotations in bindings:
            apps.tool(
                resource_uri=APP_URI,
                visibility=APP_ONLY,
                name=function.__name__,
                description=f"{description} Only for the Gandi app.",
                annotations=annotations,
            )(function)

    async def open_gandi_app(self) -> dict[str, Any]:
        """Show the MCP App, with the accounts."""
        return await self._tools.guard(self._tools.listing)

    async def app_list_accounts(self, ctx: Context[Any, Any]) -> dict[str, Any]:
        """List the accounts."""
        return await self._app(ctx, self._tools.listing)

    async def app_add_account(
        self,
        name: AccountNameParameter,
        environment: EnvironmentParameter,
        token: TokenParameter,
        ctx: Context[Any, Any],
        read_only: ReadOnlyParameter = False,
    ) -> dict[str, Any]:
        """Add an account with the token typed by the user."""

        async def run() -> dict[str, Any]:
            draft = AccountDraft(AccountName(name), Environment(environment), read_only)
            return verified(await self._accounts.add(draft, PersonalAccessToken(token)))

        return await self._app(ctx, run)

    async def app_update_account(
        self,
        name: AccountNameParameter,
        ctx: Context[Any, Any],
        *,
        new_name: str | None = None,
        read_only: bool | None = None,
        make_default: bool = False,
    ) -> dict[str, Any]:
        """Change an account; the App asked the user before allowing writes."""
        return await self._app(
            ctx,
            lambda: self._tools.update(
                name,
                new_name=new_name,
                read_only=read_only,
                make_default=make_default,
                context=self._context(),
            ),
        )

    async def app_replace_account_token(
        self, name: AccountNameParameter, token: TokenParameter, ctx: Context[Any, Any]
    ) -> dict[str, Any]:
        """Replace the token of an account."""

        async def run() -> dict[str, Any]:
            return verified(
                await self._accounts.replace_token(AccountName(name), PersonalAccessToken(token))
            )

        return await self._app(ctx, run)

    async def app_change_account_environment(
        self,
        name: AccountNameParameter,
        environment: EnvironmentParameter,
        token: TokenParameter,
        ctx: Context[Any, Any],
    ) -> dict[str, Any]:
        """Move an account to another environment with a token valid there."""

        async def run() -> dict[str, Any]:
            return verified(
                await self._accounts.change_environment(
                    AccountName(name), Environment(environment), PersonalAccessToken(token)
                )
            )

        return await self._app(ctx, run)

    async def app_remove_account(
        self, name: AccountNameParameter, ctx: Context[Any, Any]
    ) -> dict[str, Any]:
        """Remove an account; the App asked the user first."""
        return await self._app(ctx, lambda: self._tools.remove(name, self._context()))

    def _context(self) -> ConfirmationContext:
        return ConfirmationContext(from_app=True, locale=self._translator.default_locale)

    async def _app(
        self, ctx: Context[Any, Any], action: Callable[[], Awaitable[dict[str, Any]]]
    ) -> dict[str, Any]:
        async def checked() -> dict[str, Any]:
            if not client_supports_apps(ctx):
                raise AppOnlyToolError
            return await action()

        return await self._tools.guard(checked)
