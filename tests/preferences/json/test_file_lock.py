# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration tests of the preferences lock, within a process and across processes."""

import subprocess
import sys
import time
from pathlib import Path

import pytest

from gandi_mcp.preferences.exceptions import PreferencesUnavailableError
from gandi_mcp.preferences.json.file_lock import FileLock

HOLDER = """
import sys, time
from pathlib import Path
from gandi_mcp.preferences.json.file_lock import FileLock
with FileLock(Path(sys.argv[1]), 5):
    Path(sys.argv[2]).write_text("locked", encoding="utf-8")
    time.sleep(float(sys.argv[3]))
"""


def test_lock_is_exclusive_and_released(tmp_path: Path) -> None:
    path = tmp_path / "preferences.json.lock"

    with FileLock(path, 1), pytest.raises(PreferencesUnavailableError, match="another"):
        FileLock(path, 0.2).acquire()
    with FileLock(path, 0.2):
        pass
    FileLock(path, 0.2).release()


def test_lock_file_that_cannot_be_opened(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")

    with pytest.raises(PreferencesUnavailableError, match="open"):
        FileLock(blocker / "preferences.json.lock", 0.2).acquire()


def test_lock_is_shared_with_other_processes(tmp_path: Path) -> None:
    path, marker = tmp_path / "preferences.json.lock", tmp_path / "marker"
    holder = subprocess.Popen(  # noqa: S603 - test-controlled arguments
        [sys.executable, "-c", HOLDER, str(path), str(marker), "3"],
        cwd=Path(__file__).resolve().parents[3],
    )
    try:
        deadline = time.monotonic() + 30
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert marker.exists()
        with pytest.raises(PreferencesUnavailableError):
            FileLock(path, 0.3).acquire()
        with FileLock(path, 15):
            assert holder.wait(timeout=30) == 0
    finally:
        holder.wait(timeout=30)
    assert holder.returncode == 0
