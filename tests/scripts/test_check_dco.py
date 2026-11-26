# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the DCO checker, including an integration test on a temporary repository."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import check_dco as checker

GIT = shutil.which("git") or "git"


def git(repository: Path, *arguments: str) -> None:
    subprocess.run([GIT, "-C", str(repository), *arguments], check=True, capture_output=True)  # noqa: S603


@pytest.mark.parametrize(
    ("message", "signed"),
    [
        ("Fix\n\nSigned-off-by: Dev <dev@example.org>\n", True),
        ("Fix\n\nSigned-off-by: Dev <DEV@example.org>", True),
        ("Fix\n\nSigned-off-by: Other <other@example.org>\n", False),
        ("Fix\n", False),
    ],
)
def test_is_signed_off(message: str, signed: bool) -> None:
    commit = checker.Commit(sha="0" * 40, author_email="dev@example.org", message=message)

    assert checker.is_signed_off(commit) is signed


def test_usage_error() -> None:
    assert checker.main([]) == 2


def test_checks_a_real_range(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Inside a Git hook, these variables point to the outer repository.
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        monkeypatch.delenv(name)
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Dev")
    git(tmp_path, "config", "user.email", "dev@example.org")
    git(tmp_path, "config", "commit.gpgsign", "false")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    git(tmp_path, "tag", "base")
    git(tmp_path, "commit", "-q", "--allow-empty", "-s", "-m", "signed")
    monkeypatch.chdir(tmp_path)

    assert checker.main(["base..HEAD"]) == 0

    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "unsigned")

    assert checker.main(["base..HEAD"]) == 1
