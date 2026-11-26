# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the JSON preferences store on temporary files."""

import json
from pathlib import Path

import pytest

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.preferences.exceptions import CorruptPreferencesError, PreferencesUnavailableError
from gandi_mcp.preferences.json import json_preferences_store as module
from gandi_mcp.preferences.json.json_preferences_store import JsonPreferencesStore
from gandi_mcp.preferences.preferences import Preferences

pytestmark = pytest.mark.anyio

PREFERENCES = Preferences(
    (
        Account(AccountName("Société"), Environment.SANDBOX, False, "k1"),
        Account(AccountName("Pro"), Environment.PRODUCTION, True, "k2"),
    ),
    AccountName("Pro"),
)


async def test_missing_file_means_empty_preferences(tmp_path: Path) -> None:
    assert await JsonPreferencesStore(tmp_path / "absent.json").load() == Preferences()


async def test_round_trip_creates_the_directory(tmp_path: Path) -> None:
    path = tmp_path / "config" / "gandi-mcp" / "preferences.json"
    store = JsonPreferencesStore(path)

    await store.save(PREFERENCES)

    assert await store.load() == PREFERENCES
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["version"] == 1
    assert document["default_account"] == "Pro"
    assert "Société" in path.read_text(encoding="utf-8")
    assert list(path.parent.iterdir()) == [path]


async def test_saving_empty_preferences(tmp_path: Path) -> None:
    store = JsonPreferencesStore(tmp_path / "preferences.json")

    await store.save(Preferences())

    assert await store.load() == Preferences()


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        "[]",
        '{"version": 2, "accounts": []}',
        '{"accounts": []}',
        '{"version": 1, "accounts": {}}',
        '{"version": 1, "accounts": [], "default_account": 3}',
        '{"version": 1, "accounts": [], "default_account": "  "}',
        '{"version": 1, "accounts": [1], "default_account": null}',
        '{"version": 1, "accounts": [{"name": "A", "environment": "sandbox",'
        ' "read_only": false}], "default_account": "A"}',
        '{"version": 1, "accounts": [{"name": "A", "environment": "moon",'
        ' "read_only": false, "secret_key": "k"}], "default_account": "A"}',
        '{"version": 1, "accounts": [{"name": "A_", "environment": "sandbox",'
        ' "read_only": false, "secret_key": "k"}], "default_account": "A_"}',
        '{"version": 1, "accounts": [{"name": "A", "environment": "sandbox",'
        ' "read_only": "no", "secret_key": "k"}], "default_account": "A"}',
        '{"version": 1, "accounts": [{"name": "A", "environment": "sandbox",'
        ' "read_only": false, "secret_key": "k"}], "default_account": "B"}',
    ],
)
async def test_corrupt_file_is_refused_and_kept(tmp_path: Path, content: str) -> None:
    path = tmp_path / "preferences.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(CorruptPreferencesError):
        await JsonPreferencesStore(path).load()
    assert path.read_text(encoding="utf-8") == content


async def test_oversized_file_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "preferences.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(module, "MAX_FILE_SIZE", 1)

    with pytest.raises(CorruptPreferencesError):
        await JsonPreferencesStore(path).load()


async def test_invalid_encoding_is_unavailable(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(PreferencesUnavailableError):
        await JsonPreferencesStore(path).load()


async def test_unwritable_location(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")

    with pytest.raises(PreferencesUnavailableError):
        await JsonPreferencesStore(blocker / "preferences.json").save(PREFERENCES)


async def test_failed_replace_keeps_the_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "preferences.json"
    store = JsonPreferencesStore(path)
    await store.save(Preferences())
    previous = path.read_text(encoding="utf-8")

    def fail(_self: Path, _target: Path) -> Path:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "replace", fail)

    with pytest.raises(PreferencesUnavailableError):
        await store.save(PREFERENCES)
    assert path.read_text(encoding="utf-8") == previous
    assert list(tmp_path.iterdir()) == [path]
