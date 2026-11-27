# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dependency injection container: the single place where implementations are chosen."""

from dependency_injector import containers, providers

from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.accounts.gandi.gandi_organization_directory import GandiOrganizationDirectory
from gandi_mcp.accounts.gandi.gandi_token_verifier import GandiTokenVerifier
from gandi_mcp.accounts.organization_service import OrganizationService
from gandi_mcp.confirmation.channels.elicitation_channel import ElicitationChannel
from gandi_mcp.confirmation.channels.local_link_channel import LocalLinkChannel
from gandi_mcp.confirmation.confirmation_service import ConfirmationService
from gandi_mcp.confirmation.pending_confirmations import PendingConfirmations
from gandi_mcp.content.long_text_filter import LongTextFilter
from gandi_mcp.domains.contacts.contact_redactor import ContactRedactor
from gandi_mcp.domains.quotes.gandi.gandi_quote_provider import GandiQuoteProvider
from gandi_mcp.gandi.http.http_gandi_client import HttpGandiClient
from gandi_mcp.i18n.babel.babel_translator import BabelTranslator, default_locales_directory
from gandi_mcp.interaction.link_presenter import LinkPresenter
from gandi_mcp.interaction.system.system_browser import SystemBrowser
from gandi_mcp.local_pages.starlette.starlette_local_page_server import (
    StarletteLocalPageServer,
)
from gandi_mcp.operations.operation_executor import OperationExecutor
from gandi_mcp.operations.order_executor import OrderExecutor
from gandi_mcp.preferences.json.json_preferences_store import JsonPreferencesStore
from gandi_mcp.protocol.app.accounts_app_tools import AccountsAppTools
from gandi_mcp.protocol.app.app_resource import load_app_html
from gandi_mcp.protocol.error_presenter import ErrorPresenter
from gandi_mcp.protocol.server_factory import create_server
from gandi_mcp.protocol.tools.accounts_tools import AccountsTools
from gandi_mcp.protocol.tools.domains.availability_tools import AvailabilityTools
from gandi_mcp.protocol.tools.domains.contact_tools import ContactTools
from gandi_mcp.protocol.tools.domains.domain_order_runner import DomainOrderRunner
from gandi_mcp.protocol.tools.domains.domain_settings_tools import DomainSettingsTools
from gandi_mcp.protocol.tools.domains.domain_tool_runner import DomainToolRunner
from gandi_mcp.protocol.tools.domains.domains_tools import DomainsTools
from gandi_mcp.protocol.tools.domains.nameserver_tools import NameserverTools
from gandi_mcp.protocol.tools.domains.nameserver_write_tools import NameserverWriteTools
from gandi_mcp.protocol.tools.domains.order_tools import OrderTools
from gandi_mcp.protocol.tools.domains.redirection_tools import RedirectionTools
from gandi_mcp.protocol.tools.domains.redirection_write_tools import RedirectionWriteTools
from gandi_mcp.protocol.tools.domains.tag_tools import TagTools
from gandi_mcp.protocol.tools.domains.transfer_tools import TransferTools
from gandi_mcp.protocol.tools.domains.transfer_write_tools import TransferWriteTools
from gandi_mcp.protocol.tools.organization_tools import OrganizationTools
from gandi_mcp.secrets.keyring.keyring_secret_store import KeyringSecretStore
from gandi_mcp.token_entry.token_entry_service import TokenEntryService
from gandi_mcp.token_entry.token_entry_sessions import TokenEntrySessions
from gandi_mcp.token_entry.token_submission import TokenSubmission


def user_agent(version: str) -> str:
    """Return the ``User-Agent`` sent to Gandi."""
    return f"gandi-mcp/{version}"


class ApplicationContainer(containers.DeclarativeContainer):
    """Wire the application; every component is a singleton of the container.

    Configuration keys (see ``gandi-mcp.example.toml`` and ``docs/architecture.md``):
        ``app.version`` (str, required): application version, set by the entry point.
        ``app.locale`` (str or None, required): system language, set by the entry point.
        ``preferences.path``, ``gandi.production_url``, ``gandi.sandbox_url``,
        ``gandi.timeout_seconds``, ``confirmation.timeout_seconds``,
        ``token_entry.timeout_seconds``, ``content.max_free_input``: validated by the
        entry point.
    """

    config = providers.Configuration(strict=True)

    translator = providers.Singleton(
        BabelTranslator, default_locales_directory(), config.app.locale
    )
    secret_store = providers.Singleton(KeyringSecretStore)
    preferences_store = providers.Singleton(JsonPreferencesStore, config.preferences.path)
    gandi_client = providers.Singleton(
        HttpGandiClient,
        base_urls=providers.Dict(
            {
                Environment.PRODUCTION: config.gandi.production_url,
                Environment.SANDBOX: config.gandi.sandbox_url,
            }
        ),
        timeout_seconds=config.gandi.timeout_seconds,
        user_agent=providers.Callable(user_agent, config.app.version),
    )
    token_verifier = providers.Singleton(GandiTokenVerifier, gandi_client)
    account_service = providers.Singleton(
        AccountService, preferences_store, secret_store, token_verifier
    )

    pending_confirmations = providers.Singleton(
        PendingConfirmations, config.confirmation.timeout_seconds
    )
    token_entry_sessions = providers.Singleton(
        TokenEntrySessions, config.token_entry.timeout_seconds
    )
    local_pages = providers.Singleton(
        StarletteLocalPageServer,
        pending_confirmations,
        token_entry_sessions,
        providers.Singleton(TokenSubmission, account_service),
        translator,
        page_timeout_seconds=providers.Callable(
            max, config.confirmation.timeout_seconds, config.token_entry.timeout_seconds
        ),
    )
    link_presenter = providers.Singleton(LinkPresenter, providers.Singleton(SystemBrowser))
    confirmation = providers.Singleton(
        ConfirmationService,
        providers.List(
            providers.Singleton(ElicitationChannel, translator),
            providers.Singleton(
                LocalLinkChannel, pending_confirmations, local_pages, link_presenter, translator
            ),
        ),
        pending_confirmations,
    )
    token_entry = providers.Singleton(
        TokenEntryService, token_entry_sessions, local_pages, link_presenter, translator
    )
    operation_executor = providers.Singleton(
        OperationExecutor, account_service, secret_store, gandi_client, confirmation
    )
    long_text_filter = providers.Singleton(LongTextFilter, config.content.max_free_input)
    contact_redactor = providers.Singleton(ContactRedactor)
    error_presenter = providers.Singleton(ErrorPresenter, translator, long_text_filter)

    accounts_tools = providers.Singleton(
        AccountsTools, account_service, confirmation, token_entry, error_presenter, translator
    )
    domain_tool_runner = providers.Singleton(
        DomainToolRunner,
        operation_executor,
        accounts_tools,
        contact_redactor,
        long_text_filter,
    )
    order_executor = providers.Singleton(
        OrderExecutor,
        account_service,
        secret_store,
        gandi_client,
        confirmation,
        quotes=providers.Singleton(GandiQuoteProvider, gandi_client),
        translator=translator,
    )
    domain_order_runner = providers.Singleton(
        DomainOrderRunner, order_executor, accounts_tools, contact_redactor, long_text_filter
    )
    organization_service = providers.Singleton(
        OrganizationService,
        account_service,
        secret_store,
        providers.Singleton(GandiOrganizationDirectory, gandi_client),
    )
    tool_modules = providers.List(
        accounts_tools,
        providers.Singleton(OrganizationTools, organization_service, accounts_tools),
        providers.Singleton(AvailabilityTools, domain_tool_runner),
        providers.Singleton(DomainsTools, domain_tool_runner),
        providers.Singleton(NameserverTools, domain_tool_runner),
        providers.Singleton(RedirectionTools, domain_tool_runner),
        providers.Singleton(TransferTools, domain_tool_runner),
        providers.Singleton(OrderTools, domain_order_runner),
        providers.Singleton(ContactTools, domain_tool_runner),
        providers.Singleton(DomainSettingsTools, domain_tool_runner),
        providers.Singleton(NameserverWriteTools, domain_tool_runner),
        providers.Singleton(RedirectionWriteTools, domain_tool_runner),
        providers.Singleton(TagTools, domain_tool_runner),
        providers.Singleton(TransferWriteTools, domain_tool_runner),
    )

    accounts_app_tools = providers.Singleton(
        AccountsAppTools,
        account_service,
        accounts_tools,
        translator,
        providers.Callable(load_app_html),
    )

    server = providers.Singleton(
        create_server,
        version=config.app.version,
        tool_modules=tool_modules,
        app_modules=providers.List(accounts_app_tools),
        closers=providers.List(gandi_client.provided.close, local_pages.provided.close),
    )
