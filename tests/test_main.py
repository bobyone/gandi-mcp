# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the entry point."""

import tomllib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gandi_mcp import __version__, main
from gandi_mcp.i18n.system_locale import system_locale
from gandi_mcp.main import (
    PRODUCTION_URL,
    SANDBOX_URL,
    ConfigurationError,
    build_container,
    default_preferences_path,
    default_work_directory,
    load_configuration,
)

ROOT = Path(__file__).resolve().parents[1]


def write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "gandi-mcp.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_defaults_without_configuration_file() -> None:
    assert load_configuration(None) == {
        "app": {"version": __version__, "locale": system_locale()},
        "logging": {"level": "WARNING"},
        "preferences": {"path": default_preferences_path()},
        "gandi": {
            "production_url": PRODUCTION_URL,
            "sandbox_url": SANDBOX_URL,
            "timeout_seconds": 30.0,
        },
        "confirmation": {"timeout_seconds": 300},
        "token_entry": {"timeout_seconds": 600},
        "content": {"max_free_input": 280},
        "files": {"work_directory": default_work_directory(), "max_zone_file_size": 1_048_576},
    }


def test_default_work_directory_is_in_the_user_data_directory() -> None:
    path = default_work_directory()

    assert path.name == "files"
    assert path.parent.name == "gandi-mcp"


def test_default_preferences_path_is_in_the_user_configuration_directory() -> None:
    path = default_preferences_path()

    assert path.name == "preferences.json"
    assert path.parent.name == "gandi-mcp"


def test_example_file_gives_the_defaults() -> None:
    configuration = load_configuration(ROOT / "gandi-mcp.example.toml")

    assert configuration == load_configuration(None)


def test_example_file_lists_every_section() -> None:
    with (ROOT / "gandi-mcp.example.toml").open("rb") as stream:
        sections = set(tomllib.load(stream))

    assert sections == {setting.section for setting in main.SETTINGS}


def test_reads_values_from_file(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        '[logging]\nlevel = "debug"\n'
        '[preferences]\npath = "~/prefs.json"\n'
        '[gandi]\nsandbox_url = "http://127.0.0.1:8080/v5"\ntimeout_seconds = 5\n'
        "[confirmation]\ntimeout_seconds = 60\n",
    )

    configuration = load_configuration(path)

    assert configuration["logging"]["level"] == "DEBUG"
    assert configuration["preferences"]["path"] == Path("~/prefs.json").expanduser()
    assert configuration["gandi"]["sandbox_url"] == "http://127.0.0.1:8080/v5/"
    assert configuration["gandi"]["timeout_seconds"] == 5.0
    assert configuration["confirmation"]["timeout_seconds"] == 60


@pytest.mark.parametrize(
    "content",
    [
        '[logging]\nlevel = "LOUD"\n',
        'logging = "INFO"\n',
        "not = [toml\n",
        "[unknown]\nkey = 1\n",
        "[gandi]\nretries = 3\n",
        '[preferences]\npath = ""\n',
        "[preferences]\npath = 3\n",
        '[gandi]\nproduction_url = "http://api.gandi.net/v5/"\n',
        '[gandi]\nproduction_url = "https://api.gandi.net/v5/?a=1"\n',
        '[gandi]\nproduction_url = "https:///v5/"\n',
        "[gandi]\nproduction_url = 1\n",
        "[gandi]\ntimeout_seconds = 0\n",
        "[gandi]\ntimeout_seconds = true\n",
        '[gandi]\ntimeout_seconds = "30"\n',
        "[confirmation]\ntimeout_seconds = 10\n",
        "[confirmation]\ntimeout_seconds = 60.5\n",
        "[token_entry]\ntimeout_seconds = 100000\n",
        "[content]\nmax_free_input = 0\n",
    ],
)
def test_rejects_invalid_configuration(tmp_path: Path, content: str) -> None:
    with pytest.raises(ConfigurationError):
        load_configuration(write(tmp_path, content))


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
