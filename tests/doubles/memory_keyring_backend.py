# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Keyring backend keeping passwords in memory, for the keyring integration tests."""

from keyring.errors import PasswordDeleteError


class MemoryKeyringBackend:
    """A ``keyring`` backend in memory; ``failure`` is raised by every call when set.

    It does not subclass ``keyring.backend.KeyringBackend``, which would register it
    as a candidate system backend.
    """

    def __init__(self) -> None:
        self.passwords: dict[tuple[str, str], str] = {}
        self.failure: Exception | None = None

    def _check(self) -> None:
        if self.failure is not None:
            raise self.failure

    def get_password(self, service: str, username: str) -> str | None:
        self._check()
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._check()
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._check()
        if self.passwords.pop((service, username), None) is None:
            raise PasswordDeleteError(username)
