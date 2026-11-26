# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the keyring secret store, on a memory backend and the real keyring."""

import uuid

import keyring
import pytest
from keyring.errors import KeyringLocked, NoKeyringError

from gandi_mcp.secrets.exceptions import SecretNotFoundError, SecretStoreUnavailableError
from gandi_mcp.secrets.keyring.keyring_secret_store import KeyringSecretStore
from gandi_mcp.secrets.personal_access_token import PersonalAccessToken
from tests.doubles.memory_keyring_backend import MemoryKeyringBackend

pytestmark = pytest.mark.anyio

TOKEN = PersonalAccessToken("pat_0123456789abcdef")


@pytest.fixture
def backend() -> MemoryKeyringBackend:
    return MemoryKeyringBackend()


async def test_stores_reads_and_deletes(backend: MemoryKeyringBackend) -> None:
    store = KeyringSecretStore("gandi-mcp", backend)

    await store.put("key-1", TOKEN)

    assert backend.passwords == {("gandi-mcp", "key-1"): TOKEN.reveal()}
    assert await store.get("key-1") == TOKEN
    await store.delete("key-1")
    assert backend.passwords == {}


async def test_missing_secret(backend: MemoryKeyringBackend) -> None:
    store = KeyringSecretStore("gandi-mcp", backend)

    with pytest.raises(SecretNotFoundError):
        await store.get("absent")
    with pytest.raises(SecretNotFoundError):
        await store.delete("absent")


@pytest.mark.parametrize(
    "failure", [NoKeyringError("none"), KeyringLocked("locked"), RuntimeError("dbus"), OSError()]
)
async def test_unavailable_keyring(backend: MemoryKeyringBackend, failure: Exception) -> None:
    backend.failure = failure
    store = KeyringSecretStore("gandi-mcp", backend)

    for call in (store.get("k"), store.put("k", TOKEN), store.delete("k")):
        with pytest.raises(SecretStoreUnavailableError) as raised:
            await call
        assert TOKEN.reveal() not in str(raised.value)


async def test_uses_the_system_keyring_by_default(
    backend: MemoryKeyringBackend, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(keyring, "get_keyring", lambda: backend)

    await KeyringSecretStore().put("key", TOKEN)

    assert backend.passwords == {("gandi-mcp", "key"): TOKEN.reveal()}


def system_keyring_available() -> bool:
    try:
        keyring.get_password("gandi-mcp-test", "probe")
        priority = float(keyring.get_keyring().priority)
    except Exception:  # any failure means unavailable
        return False
    return priority > 0


@pytest.mark.skipif(not system_keyring_available(), reason="no usable system keyring")
async def test_round_trip_on_the_system_keyring() -> None:
    store = KeyringSecretStore("gandi-mcp-test")
    key = f"test-{uuid.uuid4()}"

    await store.put(key, TOKEN)
    try:
        assert await store.get(key) == TOKEN
    finally:
        await store.delete(key)
    with pytest.raises(SecretNotFoundError):
        await store.get(key)
