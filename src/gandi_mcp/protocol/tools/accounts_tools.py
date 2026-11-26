# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Model tools managing the accounts; none of them ever receives or returns a token."""

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp_types import ToolAnnotations
from pydantic import Field

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.account_summary import AccountSummary
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import DuplicateAccountError
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import N_
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.operations.operation_category import OperationCategory
from gandi_mcp.protocol.error_presenter import ErrorPresenter
from gandi_mcp.protocol.mcp_user_interaction import McpUserInteraction
from gandi_mcp.protocol.tool_module import ToolModule
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_target import TokenEntryTarget, TokenPurpose

REMOVE_ACCOUNT = N_("remove the account {account} and its token from this computer")
ALLOW_WRITES = N_("allow write operations on the account {account}")

AccountNameParameter = Annotated[
    str, Field(description="Account name: 1 to 40 letters, digits, hyphens or single spaces.")
]
EnvironmentParameter = Annotated[
    Literal["production", "sandbox"],
    Field(description="Gandi environment: production (real effects and costs) or sandbox."),
]
ConfirmationParameter = Annotated[
    str | None,
    Field(
        default=None,
        description="Identifier returned by a pending confirmation, once the user has "
        "answered on the page opened in their browser. Never invent one.",
        max_length=64,
    ),
]

PAGE_SHOWN_NEXT_STEP = (
    "A page to enter the Personal Access Token was shown to the user (in the client or in "
    "their browser). Never ask the user for the token in the conversation. Once the user "
    "says it is done, call list_accounts to check the result."
)
CONFIRMATION_NEXT_STEP = (
    "The user must confirm or refuse on a page shown to them (in the client or in their "
    "browser). Once they say they answered, call this tool again with the same arguments "
    "and this confirmation_id. Never invent a confirmation_id."
)


def summary(account: AccountSummary) -> dict[str, Any]:
    """Describe an account for the model, without any secret."""
    return {
        "name": str(account.name),
        "environment": account.environment.value,
        "read_only": account.read_only,
        "is_default": account.is_default,
        "removal_pending": account.removal_pending,
    }


def pending(decision: ConfirmationDecision) -> dict[str, Any]:
    """Describe a pending confirmation for the model."""
    return {
        "status": "confirmation_pending",
        "confirmation_id": decision.confirmation_id,
        "next_step": CONFIRMATION_NEXT_STEP,
    }


class AccountsTools(ToolModule):
    """``list_accounts``, ``add_account``, ``update_account``, ``replace_account_token``,
    ``change_account_environment`` and ``remove_account``.
    """

    def __init__(
        self,
        accounts: AccountService,
        confirmation: ConfirmationService,
        token_entry: TokenEntryService,
        presenter: ErrorPresenter,
        translator: Translator,
    ) -> None:
        self._accounts = accounts
        self._confirmation = confirmation
        self._token_entry = token_entry
        self._presenter = presenter
        self._translator = translator

    def register(self, server: MCPServer) -> None:
        read = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=False)
        local_write = ToolAnnotations(read_only_hint=False, open_world_hint=False)
        server.add_tool(
            self.list_accounts,
            name="list_accounts",
            title="List Gandi accounts",
            description="List the Gandi accounts configured on this computer, with their "
            "environment, read-only flag and default flag. Never returns tokens.",
            annotations=read,
        )
        server.add_tool(
            self.add_account,
            name="add_account",
            title="Add a Gandi account",
            description="Start adding a Gandi account. The Personal Access Token is never "
            "passed here: a page is shown to the user to enter it. Prefer the sandbox for "
            "tests.",
            annotations=local_write.model_copy(update={"open_world_hint": True}),
        )
        server.add_tool(
            self.update_account,
            name="update_account",
            title="Update a Gandi account",
            description="Rename an account, make it the default one, or change its read-only "
            "flag. Allowing write operations on a read-only account needs the user's "
            "confirmation.",
            annotations=local_write,
        )
        server.add_tool(
            self.replace_account_token,
            name="replace_account_token",
            title="Replace the token of a Gandi account",
            description="Start replacing the Personal Access Token of an account, for example "
            "when it expired. A page is shown to the user to enter the new token.",
            annotations=local_write.model_copy(update={"open_world_hint": True}),
        )
        server.add_tool(
            self.change_account_environment,
            name="change_account_environment",
            title="Change the environment of a Gandi account",
            description="Start moving an account between production and sandbox. A page is "
            "shown to the user to enter a token valid in the new environment.",
            annotations=local_write.model_copy(update={"open_world_hint": True}),
        )
        server.add_tool(
            self.remove_account,
            name="remove_account",
            title="Remove a Gandi account",
            description="Remove an account and its token from this computer (nothing changes "
            "at Gandi). Needs the user's confirmation; if it is pending, call again with "
            "the returned confirmation_id once the user answered.",
            annotations=ToolAnnotations(
                read_only_hint=False, destructive_hint=True, open_world_hint=False
            ),
        )

    async def list_accounts(self) -> dict[str, Any]:
        """List the accounts."""
        return await self._guard(self.listing)

    async def add_account(
        self,
        name: AccountNameParameter,
        environment: EnvironmentParameter,
        ctx: Context[Any, Any],
        read_only: Annotated[
            bool, Field(description="Refuse every write operation on this account.")
        ] = False,
    ) -> dict[str, Any]:
        """Open a token entry session for a new account."""

        async def run() -> dict[str, Any]:
            account_name = AccountName(name)
            existing = {account.name for account in await self._accounts.list()}
            if account_name in existing:
                raise DuplicateAccountError(str(account_name))
            target = TokenEntryTarget(
                TokenPurpose.ADD, account_name, Environment(environment), read_only
            )
            return await self._open_token_entry(target, ctx)

        return await self._guard(run)

    async def update_account(
        self,
        name: AccountNameParameter,
        ctx: Context[Any, Any],
        *,
        new_name: Annotated[
            str | None, Field(default=None, description="New account name.")
        ] = None,
        read_only: Annotated[
            bool | None, Field(default=None, description="New read-only flag.")
        ] = None,
        make_default: Annotated[
            bool, Field(description="Make this account the default one.")
        ] = False,
        confirmation_id: ConfirmationParameter = None,
    ) -> dict[str, Any]:
        """Rename an account, change its read-only flag or make it the default one."""
        return await self._guard(
            lambda: self.update(
                name,
                new_name=new_name,
                read_only=read_only,
                make_default=make_default,
                context=self.context(ctx),
                confirmation_id=confirmation_id,
            )
        )

    async def replace_account_token(
        self, name: AccountNameParameter, ctx: Context[Any, Any]
    ) -> dict[str, Any]:
        """Open a token entry session to replace the token of an account."""

        async def run() -> dict[str, Any]:
            account = await self._accounts.resolve(AccountName(name))
            target = TokenEntryTarget(
                TokenPurpose.REPLACE,
                account.name,
                account.environment,
                expected=account.reference,
            )
            return await self._open_token_entry(target, ctx)

        return await self._guard(run)

    async def change_account_environment(
        self,
        name: AccountNameParameter,
        environment: EnvironmentParameter,
        ctx: Context[Any, Any],
    ) -> dict[str, Any]:
        """Open a token entry session to move an account to another environment."""

        async def run() -> dict[str, Any]:
            account = await self._accounts.resolve(AccountName(name))
            target = TokenEntryTarget(
                TokenPurpose.CHANGE_ENVIRONMENT,
                account.name,
                Environment(environment),
                expected=account.reference,
            )
            return await self._open_token_entry(target, ctx)

        return await self._guard(run)

    async def remove_account(
        self,
        name: AccountNameParameter,
        ctx: Context[Any, Any],
        confirmation_id: ConfirmationParameter = None,
    ) -> dict[str, Any]:
        """Remove an account after the user's confirmation."""
        return await self._guard(lambda: self.remove(name, self.context(ctx), confirmation_id))

    async def update(
        self,
        name: str,
        *,
        new_name: str | None,
        read_only: bool | None,
        make_default: bool,
        context: ConfirmationContext,
        confirmation_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply account changes; allowing writes on a read-only account is confirmed."""
        account = await self._accounts.resolve(AccountName(name))
        target_name = AccountName(new_name) if new_name is not None else account.name
        writes_confirmed = read_only is False and account.read_only
        if writes_confirmed:
            request = ConfirmationRequest(
                f"accounts.allow_writes:{account.reference.fingerprint()}",
                OperationCategory.WRITE,
                LocalizedText(ALLOW_WRITES, {"account": str(account.name)}),
                account.name,
                account.environment,
            )
            decision = await self._confirmation.confirm(request, context, confirmation_id)
            if not decision.accepted:
                return pending(decision)
        result = await self._accounts.update(
            account.name,
            new_name=target_name,
            read_only=read_only,
            make_default=make_default,
            expected=account.reference,
            writes_confirmed=writes_confirmed,
        )
        return {"status": "updated", "account": summary(result)}

    async def remove(
        self, name: str, context: ConfirmationContext, confirmation_id: str | None = None
    ) -> dict[str, Any]:
        """Remove an account once the user confirmed it; also finishes a pending removal."""
        account = await self._accounts.resolve(AccountName(name), allow_pending=True)
        request = ConfirmationRequest(
            f"accounts.remove:{account.reference.fingerprint()}",
            OperationCategory.DESTRUCTIVE,
            LocalizedText(REMOVE_ACCOUNT, {"account": str(account.name)}),
            account.name,
            account.environment,
        )
        decision = await self._confirmation.confirm(request, context, confirmation_id)
        if not decision.accepted:
            return pending(decision)
        removal = await self._accounts.remove(account.name, account.reference)
        return {
            "status": "removed",
            "account": str(removal.removed),
            "new_default_account": str(removal.new_default) if removal.new_default else None,
        }

    async def listing(self) -> dict[str, Any]:
        """Describe every account for the model or the MCP App."""
        return {"accounts": [summary(account) for account in await self._accounts.list()]}

    async def guard(self, action: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
        """Run an action, turning business errors into explained tool errors."""
        return await self._guard(action)

    async def _open_token_entry(
        self, target: TokenEntryTarget, ctx: Context[Any, Any]
    ) -> dict[str, Any]:
        await self._token_entry.start(
            target, McpUserInteraction(ctx), self._translator.default_locale
        )
        return {
            "status": "token_entry_page_shown",
            "account": str(target.name),
            "environment": target.environment.value,
            "next_step": PAGE_SHOWN_NEXT_STEP,
        }

    def context(self, ctx: Context[Any, Any]) -> ConfirmationContext:
        """How the user can be reached for this call: elicitation, else a local page."""
        return ConfirmationContext(McpUserInteraction(ctx), locale=self._translator.default_locale)

    async def _guard(self, action: Callable[[], Awaitable[dict[str, Any]]]) -> dict[str, Any]:
        try:
            return await action()
        except Exception as error:
            raise self._presenter.tool_error(error, self._translator.default_locale) from error
