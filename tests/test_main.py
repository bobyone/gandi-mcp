# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the entry point."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gandi_mcp import __version__, main
from gandi_mcp.main import ConfigurationError, build_container, load_configuration


def test_defaults_without_configuration_file() -> None:
    assert load_configuration(None) == {
        "app": {"version": __version__},
        "logging": {"level": "WARNING"},
    }


def test_reads_log_level_from_file(tmp_path: Path) -> None:
    path = tmp_path / "gandi-mcp.toml"
    path.write_text('[logging]\nlevel = "debug"\n', encoding="utf-8")

    assert load_configuration(path)["logging"]["level"] == "DEBUG"


@pytest.mark.parametrize(
    "content",
    ['[logging]\nlevel = "LOUD"\n', 'logging = "INFO"\n', "not = [toml\n"],
)
def test_rejects_invalid_configuration(tmp_path: Path, content: str) -> None:
    path = tmp_path / "gandi-mcp.toml"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_configuration(path)


def test_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError):
        load_configuration(tmp_path / "missing.toml")


def test_container_builds_server_once() -> None:
    container = build_container(load_configuration(None))

    assert container.server() is container.server()
    assert container.server().version == __version__


def test_main_runs_server_over_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    server = MagicMock()
    container = MagicMock()
    container.server.return_value = server
    monkeypatch.setattr(main, "build_container", lambda _configuration: container)

    main.main([])

    server.run.assert_called_once_with("stdio")


def test_main_exits_on_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as raised:
        main.main(["--config", str(tmp_path / "missing.toml")])

    assert raised.value.code == 2
