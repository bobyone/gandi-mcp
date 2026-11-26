# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Run orders: quote, dry run, confirmation bound to the quote and token, price re-check."""

import hmac
import logging
from secrets import token_bytes

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.exceptions import AccountChangedError, ReadOnlyAccountError
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.confirmation.confirmation_context import ConfirmationContext
from gandi_mcp.confirmation.confirmation_decision import ConfirmationDecision
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.exceptions import SecretInputMissingError
from gandi_mcp.domains.quotes.quote import Quote
from gandi_mcp.domains.quotes.quote_provider import QuoteProvider
from gandi_mcp.gandi.exceptions import GandiError
from gandi_mcp.gandi.gandi_client import GandiClient
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.i18n.message import N_
from gandi_mcp.i18n.translator import Translator
from gandi_mcp.operations.billable_operation import BillableOperation
from gandi_mcp.operations.dry_run import dry_run_details
from gandi_mcp.operations.exceptions import DryRunRejectedError, PriceChangedError
from gandi_mcp.operations.secret_echo import scrubbed, without_details
from gandi_mcp.operations.untrusted_result import UntrustedResult
from gandi_mcp.operations.write_access import still_writable
from gandi_mcp.secrets.secret_store import SecretStore

PRICE_FOR_ORGANIZATION = N_("{price}, paid by the organization {organization}")

logger = logging.getLogger(__name__)


class OrderExecutor:
    """Apply the order rules (algorithm G, ADR 7), then buy.

    1. Resolve the account; refuse a read-only one. The paying organization is the
       one given, else the account preference, else none.
    2. Quote the order.
    3. Check it with a dry run when Gandi supports one (first call only).
    4. Ask for a confirmation bound to the operation, the account, the token, the
       price, its currency and the paying organization; the description shows the price.
    5. Quote again: any difference cancels the order.
    6. Order at the accepted price.
    """

    def __init__(
        self,
        accounts: AccountService,
        secrets: SecretStore,
        client: GandiClient,
        confirmation: ConfirmationService,
        *,
        quotes: QuoteProvider,
        translator: Translator,
    ) -> None:
        self._accounts = accounts
        self._secrets = secrets
        self._client = client
        self._confirmation = confirmation
        self._quotes = quotes
        self._translator = translator
        self._confirmation_key = token_bytes(32)

    async def run(
        self,
        operation: BillableOperation,
        account_name: AccountName | None,
        context: ConfirmationContext,
        confirmation_id: str | None = None,
        paying_organization: OrganizationId | None = None,
    ) -> UntrustedResult | ConfirmationDecision:
        """Order, or return a pending confirmation to resume with its identifier.

        Raises:
            NoAccountError, AccountNotFoundError, AccountChangedError, ReadOnlyAccountError,
            QuoteError, DryRunRejectedError, ConfirmationError, PriceChangedError,
            SecretStoreError, GandiError.
        """
        account = await self._accounts.resolve(account_name)
        if account.read_only:
            raise ReadOnlyAccountError(f"the account {account.name} is read-only")
        organization = paying_organization or account.paying_organization
        token = await self._secrets.get(account.secret_key)
        request = operation.quote_request(organization)
        quote = await self._quotes.quote(account.environment, token, request)
        if confirmation_id is None and operation.supports_dry_run:
            checked = await operation.order(
                self._client, account.environment, token, quote, dry_run=True
            )
            details = dry_run_details(checked)
            if details is not None:
                raise DryRunRejectedError("Gandi refused the order when checking it", details)
        secret_input = operation.secret_input()
        # Pending confirmations live in memory, so the key only needs to live
        # as long as this executor. The subject never contains the token itself.
        token_fingerprint = hmac.digest(
            self._confirmation_key, token.reveal().encode("ascii"), "sha256"
        ).hex()
        decision = await self._confirmation.confirm(
            ConfirmationRequest(
                "@".join(
                    (
                        operation.subject(),
                        account.reference.fingerprint(),
                        token_fingerprint,
                        str(quote.price.amount),
                        quote.price.currency,
                        str(organization or ""),
                    )
                ),
                operation.category,
                self._described(operation, quote, context),
                account.name,
                account.environment,
                secret_input,
            ),
            context,
            confirmation_id,
        )
        if not decision.accepted:
            return decision
        if secret_input is not None and decision.secret is None:
            raise SecretInputMissingError(f"{operation.name} needs a secret")
        current = await self._quotes.quote(account.environment, token, request)
        if current.price != quote.price:
            raise PriceChangedError("the price changed since the confirmation")
        # Same account and same credential as the confirmed quote; the write access is
        # checked again last, right before the request (the keyring read may wait).
        account = await still_writable(self._accounts, account)
        if await self._secrets.get(account.secret_key) != token:
            raise AccountChangedError(f"the token of {account.name} changed meanwhile")
        account = await still_writable(self._accounts, account)
        secret = decision.secret
        try:
            response = await operation.order(
                self._client, account.environment, token, quote, secret=secret
            )
        except GandiError as error:
            if secret is not None:
                raise without_details(error) from None
            raise
        logger.info("order %s done (%s)", operation.name, account.environment.value)
        data = scrubbed(response.data, secret) if secret is not None else response.data
        return UntrustedResult(data, response.total_count, response.filtered_count)

    def _described(
        self, operation: BillableOperation, quote: Quote, context: ConfirmationContext
    ) -> LocalizedText:
        price = self._translator.format_money(
            quote.price.amount, quote.price.currency, context.locale
        )
        organization = quote.request.paying_organization
        if organization is not None:
            price = self._translator.translate(
                PRICE_FOR_ORGANIZATION, context.locale, price=price, organization=str(organization)
            )
        description = operation.describe()
        return LocalizedText(description.message, {**description.params, "price": price})
