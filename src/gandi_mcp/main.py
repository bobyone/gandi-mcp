# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Entry point of the personal mode: reads configuration once, wires and runs the server."""

import argparse
import logging
import sys
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import platformdirs

from gandi_mcp import __version__
from gandi_mcp.container import ApplicationContainer
from gandi_mcp.i18n.system_locale import system_locale

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DEFAULT_LOG_LEVEL = "WARNING"
APPLICATION_DIRECTORY = "gandi-mcp"
PREFERENCES_FILE = "preferences.json"
PRODUCTION_URL = "https://api.gandi.net/v5/"
SANDBOX_URL = "https://api.sandbox.gandi.net/v5/"
LOCALHOST_NAMES = frozenset({"localhost", "127.0.0.1", "::1"})

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when the configuration file is missing or invalid."""


def default_preferences_path() -> Path:
    """Return the preferences file in the user configuration directory of the OS."""
    directory = platformdirs.user_config_path(APPLICATION_DIRECTORY, appauthor=False, roaming=True)
    return directory / PREFERENCES_FILE


def _log_level(name: str, value: object) -> str:
    level = str(value).upper()
    if level not in LOG_LEVELS:
        raise ConfigurationError(f"{name} must be one of {', '.join(LOG_LEVELS)}")
    return level


def _path(name: str, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{name} must be a non-empty path")
    return Path(value).expanduser()


def _base_url(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{name} must be a URL")
    parts = urlsplit(value)
    secure = parts.scheme == "https" or (
        parts.scheme == "http" and parts.hostname in LOCALHOST_NAMES
    )
    if not secure or not parts.hostname or parts.query or parts.fragment:
        raise ConfigurationError(f"{name} must be an https URL without query nor fragment")
    return value if value.endswith("/") else value + "/"


def _bounded_number(minimum: float, maximum: float) -> Callable[[str, object], float]:
    def convert(name: str, value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise ConfigurationError(f"{name} must be a number")
        if not minimum <= value <= maximum:
            raise ConfigurationError(f"{name} must be between {minimum:g} and {maximum:g}")
        return float(value)

    return convert


def _bounded_integer(minimum: int, maximum: int) -> Callable[[str, object], int]:
    def convert(name: str, value: object) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigurationError(f"{name} must be an integer")
        if not minimum <= value <= maximum:
            raise ConfigurationError(f"{name} must be between {minimum} and {maximum}")
        return value

    return convert


@dataclass(frozen=True)
class Setting:
    """One optional configuration key, its default and its validation."""

    section: str
    key: str
    default: Callable[[], object]
    convert: Callable[[str, object], object]


SETTINGS = (
    Setting("logging", "level", lambda: DEFAULT_LOG_LEVEL, _log_level),
    Setting("preferences", "path", default_preferences_path, _path),
    Setting("gandi", "production_url", lambda: PRODUCTION_URL, _base_url),
    Setting("gandi", "sandbox_url", lambda: SANDBOX_URL, _base_url),
    Setting("gandi", "timeout_seconds", lambda: 30.0, _bounded_number(1, 300)),
    Setting("confirmation", "timeout_seconds", lambda: 300, _bounded_integer(30, 3600)),
    Setting("token_entry", "timeout_seconds", lambda: 600, _bounded_integer(60, 3600)),
    Setting("content", "max_free_input", lambda: 280, _bounded_integer(1, 10000)),
)


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="gandi-mcp", description="Gandi MCP server (stdio).")
    parser.add_argument("--config", type=Path, help="path to a TOML configuration file")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def _read_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except OSError as error:
        raise ConfigurationError(f"cannot read configuration file {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(f"invalid TOML in configuration file {path}") from error


def load_configuration(path: Path | None) -> dict[str, Any]:
    """Load and validate the configuration, applying defaults.

    Raises:
        ConfigurationError: if the file cannot be read or contains invalid values.
    """
    raw = _read_file(path) if path is not None else {}
    known = {setting.section for setting in SETTINGS}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ConfigurationError(f"unknown configuration section: {', '.join(unknown)}")
    configuration: dict[str, Any] = {"app": {"version": __version__, "locale": system_locale()}}
    for setting in SETTINGS:
        section = raw.get(setting.section, {})
        if not isinstance(section, dict):
            raise ConfigurationError(f"[{setting.section}] must be a table")
        name = f"{setting.section}.{setting.key}"
        value = (
            setting.convert(name, section[setting.key])
            if setting.key in section
            else setting.default()
        )
        configuration.setdefault(setting.section, {})[setting.key] = value
    for section_name in known & set(raw):
        allowed = {s.key for s in SETTINGS if s.section == section_name}
        extra = sorted(set(raw[section_name]) - allowed)
        if extra:
            raise ConfigurationError(f"unknown key in [{section_name}]: {', '.join(extra)}")
    return configuration


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
