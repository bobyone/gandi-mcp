# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Organizations of an account and its paying organization."""

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.account_summary import AccountSummary
from gandi_mcp.accounts.exceptions import UnknownOrganizationError
from gandi_mcp.accounts.organization import Organization
from gandi_mcp.accounts.organization_directory import OrganizationDirectory
from gandi_mcp.accounts.organization_id import OrganizationId
from gandi_mcp.secrets.secret_store import SecretStore


class OrganizationService:
    """List the organizations an account can use and choose the one that pays.

    The paying organization is a local preference of the account (no Gandi write):
    orders use it unless they name another one.
    """

    def __init__(
        self, accounts: AccountService, secrets: SecretStore, directory: OrganizationDirectory
    ) -> None:
        self._accounts = accounts
        self._secrets = secrets
        self._directory = directory

    async def organizations(self, name: AccountName | None) -> tuple[Organization, ...]:
        """List the organizations of the named account, or of the default one.

        Raises:
            NoAccountError, AccountNotFoundError, AccountRemovalPendingError,
            SecretStoreError, GandiError.
        """
        account = await self._accounts.resolve(name)
        token = await self._secrets.get(account.secret_key)
        return await self._directory.organizations(account.environment, token)

    async def set_paying_organization(
        self, name: AccountName | None, organization: OrganizationId | None
    ) -> AccountSummary:
        """Make an organization of the account its paying one; ``None`` clears it.

        Raises:
            UnknownOrganizationError: if the account cannot use this organization.
            NoAccountError, AccountNotFoundError, AccountChangedError,
            SecretStoreError, GandiError, PreferencesError.
        """
        account = await self._accounts.resolve(name)
        if organization is not None:
            known = {item.id for item in await self.organizations(account.name)}
            if organization not in known:
                raise UnknownOrganizationError("the account cannot use this organization")
        return await self._accounts.update(
            account.name, paying_organization=organization, expected=account.reference
        )
