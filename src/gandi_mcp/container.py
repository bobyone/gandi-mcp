# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Dependency injection container: the single place where implementations are chosen."""

from dependency_injector import containers, providers

from gandi_mcp.protocol.server_factory import create_server


class ApplicationContainer(containers.DeclarativeContainer):
    """Wire the application.

    Configuration keys (see ``config.example.toml``):
        ``app.version`` (str, required): application version, set by the entry point.
        ``logging.level`` (str, optional, default ``WARNING``): log level.
    """

    config = providers.Configuration(strict=True)

    server = providers.Singleton(create_server, version=config.app.version)
