# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run operations with the transverse rules: account, read-only, confirmation, token."""

import logging

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.exceptions import ReadOnlyAccountError
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.gandi.gandi_response import SEE_OTHER
from gandi_mcp.operations.operation import Operation
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.secrets.secret_store import SecretStore

logger = logging.getLogger(__name__)


class OperationExecutor:
    """Apply the rules every operation follows, then call Gandi.

    1. Resolve the account (named, otherwise the default one).
    2. Refuse a write operation on a read-only account.
    3. Ask for a confirmation before a destructive or billable operation, bound to
       the operation, its parameters, the account identity and its environment.
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
        if operation.category.needs_confirmation:
            request = ConfirmationRequest(
                f"{operation.subject()}@{account.reference.fingerprint()}",
                operation.category,
                operation.describe(),
                account.name,
                account.environment,
            )
            decision = await self._confirmation.confirm(request, context, confirmation_id)
            if not decision.accepted:
                return decision
        token = await self._secrets.get(account.secret_key)
        response = await operation.execute(self._client, account.environment, token)
        logger.info("operation %s done (%s)", operation.name, account.environment.value)
        return UntrustedResult(
            response.data,
            response.total_count,
            response.filtered_count,
            completed=response.status == SEE_OTHER,
        )
