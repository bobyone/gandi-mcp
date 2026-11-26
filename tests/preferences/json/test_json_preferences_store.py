# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the JSON preferences store on temporary files."""

import asyncio
import json
import threading
from pathlib import Path

import pytest

from gandi_mcp.accounts.account import Account
from gandi_mcp.accounts.account_draft import AccountDraft
from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.account_service import AccountService
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.preferences.exceptions import CorruptPreferencesError, PreferencesUnavailableError
from gandi_mcp.preferences.json import json_preferences_store as module
from gandi_mcp.preferences.json.json_preferences_store import JsonPreferencesStore
from gandi_mcp.preferences.preferences import Preferences
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.in_memory_secret_store import InMemorySecretStore
from tests.doubles.stub_token_verifier import StubTokenVerifier

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


async def test_concurrent_processes_never_lose_an_account(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    token = PersonalAccessToken("pat_sandbox_0123456789")
    secrets, verifier = InMemorySecretStore(), StubTokenVerifier()
    verifier.accept(Environment.SANDBOX, token)
    # Two services with their own store on the same file, as two server processes.
    services = [AccountService(JsonPreferencesStore(path), secrets, verifier) for _ in range(2)]

    await asyncio.gather(
        *(
            service.add(AccountDraft(AccountName(f"Account {index}"), Environment.SANDBOX), token)
            for index, service in enumerate(services * 3)
        )
    )

    names = {str(account.name) for account in await services[0].list()}
    assert names == {f"Account {index}" for index in range(6)}
    assert len(secrets.tokens) == 6


async def test_transaction_times_out_when_another_holds_the_lock(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    first, second = JsonPreferencesStore(path), JsonPreferencesStore(path, 0.2)

    async with first.transaction():
        with pytest.raises(PreferencesUnavailableError):
            async with second.transaction():
                pass
    async with second.transaction():
        assert await second.load() == Preferences()


async def test_cancelled_while_waiting_for_the_lock_never_leaks_it(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json"
    holder, waiter = JsonPreferencesStore(path), JsonPreferencesStore(path, 5)

    async def wait_for_the_lock() -> None:
        async with waiter.transaction():
            pytest.fail("the cancelled transaction must not run")

    async with holder.transaction():
        task = asyncio.ensure_future(wait_for_the_lock())
        await asyncio.sleep(0.2)
        task.cancel()
        await asyncio.sleep(0.05)
    with pytest.raises(asyncio.CancelledError):
        await task
    # The worker of the cancelled transaction gets the lock once it is free.
    await asyncio.sleep(0.5)

    async with JsonPreferencesStore(path, 0.5).transaction():
        pass


async def test_cancelled_during_a_write_keeps_the_lock_until_it_ends(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "preferences.json"
    store = JsonPreferencesStore(path)
    writing, release = threading.Event(), threading.Event()
    original = JsonPreferencesStore._save

    def slow_save(self: JsonPreferencesStore, preferences: Preferences) -> None:
        writing.set()
        release.wait(5)
        original(self, preferences)

    monkeypatch.setattr(JsonPreferencesStore, "_save", slow_save)

    async def change() -> None:
        async with store.transaction():
            await store.save(PREFERENCES)

    task = asyncio.ensure_future(change())
    await asyncio.to_thread(writing.wait, 5)
    task.cancel()
    await asyncio.sleep(0.05)

    with pytest.raises(PreferencesUnavailableError):
        async with JsonPreferencesStore(path, 0.2).transaction():
            pass
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    async with JsonPreferencesStore(path, 0.5).transaction():
        assert await JsonPreferencesStore(path).load() == PREFERENCES
