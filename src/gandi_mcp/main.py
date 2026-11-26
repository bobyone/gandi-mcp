# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Entry point of the personal mode: reads configuration once, wires and runs the server."""

import argparse
import logging
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from gandi_mcp import __version__
from gandi_mcp.container import ApplicationContainer

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEFAULT_LOG_LEVEL = "WARNING"

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when the configuration file is missing or invalid."""


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="gandi-mcp", description="Gandi MCP server (stdio).")
    parser.add_argument("--config", type=Path, help="path to a TOML configuration file")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def load_configuration(path: Path | None) -> dict[str, Any]:
    """Load and validate the configuration, applying defaults.

    Raises:
        ConfigurationError: if the file cannot be read or contains invalid values.
    """
    raw: dict[str, Any] = {}
    if path is not None:
        try:
            with path.open("rb") as stream:
                raw = tomllib.load(stream)
        except OSError as error:
            raise ConfigurationError(f"cannot read configuration file {path}") from error
        except tomllib.TOMLDecodeError as error:
            raise ConfigurationError(f"invalid TOML in configuration file {path}") from error

    logging_section = raw.get("logging", {})
    if not isinstance(logging_section, dict):
        raise ConfigurationError("[logging] must be a table")
    level = str(logging_section.get("level", DEFAULT_LOG_LEVEL)).upper()
    if level not in LOG_LEVELS:
        raise ConfigurationError(f"logging.level must be one of {', '.join(LOG_LEVELS)}")

    return {"app": {"version": __version__}, "logging": {"level": level}}


def configure_logging(level: str) -> None:
    """Send logs to stderr: stdout is reserved for the MCP stdio protocol."""
    logging.basicConfig(
        stream=sys.stderr,
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_container(configuration: dict[str, Any]) -> ApplicationContainer:
    """Create the container from an already validated configuration."""
    container = ApplicationContainer()
    container.config.from_dict(configuration)
    return container


def main(argv: Sequence[str] | None = None) -> None:
    """Run the MCP server over stdio."""
    arguments = parse_arguments(argv)
    try:
        configuration = load_configuration(arguments.config)
    except ConfigurationError as error:
        configure_logging(DEFAULT_LOG_LEVEL)
        logger.error("configuration error: %s", error)
        raise SystemExit(2) from error
    configure_logging(configuration["logging"]["level"])
    container = build_container(configuration)
    logger.info("starting gandi-mcp %s over stdio", __version__)
    container.server().run("stdio")
