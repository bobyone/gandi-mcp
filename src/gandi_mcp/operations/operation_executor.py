# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run operations with the transverse rules: account, read-only, confirmation, token."""

import logging

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.exceptions import ReadOnlyAccountError
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.exceptions import SecretInputMissingError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import SEE_OTHER
from gandi_mcp.operations.dry_run import dry_run_details
from gandi_mcp.operations.exceptions import DryRunRejectedError
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.secrets.secret_store import SecretStore

logger = logging.getLogger(__name__)


class OperationExecutor:
    """Apply the rules every operation follows, then call Gandi.

    1. Resolve the account (named, otherwise the default one).
    2. Refuse a write operation on a read-only account.
    3. Ask for a confirmation before a destructive or billable operation, or one
       needing a secret typed by the user, bound to the operation, its parameters,
       the account identity and its environment. A confirmed operation is first
       checked with a Gandi dry run when it offers one.
    4. Read the token and call Gandi in the account environment.
    5. Return the data, marked as untrusted.
    """

    def __init__(
        self,
        accounts: AccountService,
        secrets: SecretStore,
        client: GandiClient,
        confirmation: ConfirmationService,
    ) -> None:
        self._accounts = accounts
        self._secrets = secrets
        self._client = client
        self._confirmation = confirmation

    async def run(
        self,
        operation: Operation,
        account_name: AccountName | None,
        context: ConfirmationContext,
        confirmation_id: str | None = None,
    ) -> UntrustedResult | ConfirmationDecision:
        """Run the operation, or return a pending confirmation to resume later.

        Raises:
            NoAccountError, AccountNotFoundError, ReadOnlyAccountError,
            ConfirmationError, SecretStoreError, GandiError.
        """
        account = await self._accounts.resolve(account_name)
        if operation.category.is_write and account.read_only:
            raise ReadOnlyAccountError(f"the account {account.name} is read-only")
        secret_input = operation.secret_input()
        secret = None
        if operation.category.needs_confirmation or secret_input is not None:
            if confirmation_id is None:
                await self._check(operation, account.environment, account.secret_key)
            request = ConfirmationRequest(
                f"{operation.subject()}@{account.reference.fingerprint()}",
                operation.category,
                operation.describe(),
                account.name,
                account.environment,
                secret_input,
            )
            decision = await self._confirmation.confirm(request, context, confirmation_id)
            if not decision.accepted:
                return decision
            secret = decision.secret
            if secret_input is not None and secret is None:
                raise SecretInputMissingError(f"{operation.name} needs a secret")
        token = await self._secrets.get(account.secret_key)
        response = await operation.execute(self._client, account.environment, token, secret)
        logger.info("operation %s done (%s)", operation.name, account.environment.value)
        return UntrustedResult(
            response.data,
            response.total_count,
            response.filtered_count,
            completed=response.status == SEE_OTHER,
        )

    async def _check(self, operation: Operation, environment: Environment, key: str) -> None:
        token = await self._secrets.get(key)
        checked = await operation.check(self._client, environment, token)
        details = dry_run_details(checked) if checked is not None else None
        if details is not None:
            raise DryRunRejectedError("Gandi refused the operation when checking it", details)
