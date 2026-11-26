# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exclusive lock on a file, shared by every process of the computer."""

import os
import sys
import time
from pathlib import Path
from types import TracebackType

from gandi_mcp.preferences.exceptions import PreferencesUnavailableError

RETRY_SECONDS = 0.05


class FileLock:
    """Advisory exclusive lock held on a lock file (``msvcrt`` or ``fcntl``).

    Every gandi-mcp process using the same preferences file takes this lock around
    its read-modify-write, so that concurrent clients never lose an update. The lock
    is released when the process exits, even after a crash.
    """

    def __init__(self, path: Path, timeout_seconds: float) -> None:
        """Lock ``path`` (created if needed), waiting at most ``timeout_seconds``."""
        self._path = path
        self._timeout = timeout_seconds
        self._descriptor: int | None = None

    def acquire(self) -> None:
        """Wait for the lock.

        Raises:
            PreferencesUnavailableError: if the lock file cannot be opened, or another
                process holds the lock longer than the timeout.
        """
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self._path, os.O_RDWR | os.O_CREAT, 0o600)
        except OSError as error:
            raise PreferencesUnavailableError("cannot open the preferences lock") from error
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                self._try_lock(descriptor)
            except OSError as error:
                if time.monotonic() >= deadline:
                    os.close(descriptor)
                    raise PreferencesUnavailableError(
                        "the preferences are locked by another gandi-mcp process"
                    ) from error
                time.sleep(RETRY_SECONDS)
            else:
                self._descriptor = descriptor
                return

    def release(self) -> None:
        """Release the lock, if held."""
        descriptor, self._descriptor = self._descriptor, None
        if descriptor is None:
            return
        try:
            self._unlock(descriptor)
        finally:
            os.close(descriptor)

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        error: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()

    if sys.platform == "win32":

        @staticmethod
        def _try_lock(descriptor: int) -> None:
            import msvcrt  # noqa: PLC0415 - platform-specific module

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)

        @staticmethod
        def _unlock(descriptor: int) -> None:
            import msvcrt  # noqa: PLC0415 - platform-specific module

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)

    else:

        @staticmethod
        def _try_lock(descriptor: int) -> None:
            import fcntl  # noqa: PLC0415 - platform-specific module

            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)

        @staticmethod
        def _unlock(descriptor: int) -> None:
            import fcntl  # noqa: PLC0415 - platform-specific module

            fcntl.flock(descriptor, fcntl.LOCK_UN)
