# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the DCO checker, including integration tests on a temporary repository."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from scripts import check_dco as checker

GIT = shutil.which("git") or "git"
AUTHOR = "dev@example.org"


def git(repository: Path, *arguments: str) -> None:
    subprocess.run([GIT, "-C", str(repository), *arguments], check=True, capture_output=True)  # noqa: S603


def commit(author_email: str = AUTHOR, *sign_offs: str) -> checker.Commit:
    return checker.Commit(sha="0" * 40, author_email=author_email, sign_offs=sign_offs)


@pytest.mark.parametrize(
    ("sign_offs", "signed"),
    [
        (("Dev <dev@example.org>",), True),
        (("Dev <DEV@example.org>",), True),
        (("Other <other@example.org>", "Dev <dev@example.org>"), True),
        (("Other <other@example.org>",), False),
        (("dev@example.org",), False),
        ((), False),
    ],
)
def test_is_signed_off(sign_offs: tuple[str, ...], signed: bool) -> None:
    assert checker.is_signed_off(commit(AUTHOR, *sign_offs)) is signed


def test_usage_error() -> None:
    assert checker.main([]) == 2


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Inside a Git hook, these variables point to the outer repository.
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        monkeypatch.delenv(name)
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.name", "Dev")
    git(tmp_path, "config", "user.email", AUTHOR)
    git(tmp_path, "config", "commit.gpgsign", "false")
    git(tmp_path, "commit", "-q", "--allow-empty", "-m", "base")
    git(tmp_path, "tag", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_signed_range_passes(repository: Path) -> None:
    git(repository, "commit", "-q", "--allow-empty", "-s", "-m", "signed")

    assert checker.main(["base..HEAD"]) == 0


def test_unsigned_commit_fails(repository: Path) -> None:
    git(repository, "commit", "-q", "--allow-empty", "-m", "unsigned")

    assert checker.main(["base..HEAD"]) == 1


def test_sign_off_in_the_body_is_not_a_trailer(repository: Path) -> None:
    message = "Subject\n\nSigned-off-by: Dev <dev@example.org>\n\nA last paragraph."
    git(repository, "commit", "-q", "--allow-empty", "-m", message)

    assert checker.main(["base..HEAD"]) == 1


def test_unsigned_merge_commit_fails(repository: Path) -> None:
    git(repository, "switch", "-q", "-c", "topic")
    git(repository, "commit", "-q", "--allow-empty", "-s", "-m", "topic")
    git(repository, "switch", "-q", "main")
    git(repository, "commit", "-q", "--allow-empty", "-s", "-m", "main")
    git(repository, "merge", "-q", "--no-ff", "--no-edit", "topic")

    assert checker.main(["base..HEAD"]) == 1

    git(repository, "commit", "-q", "--amend", "--no-edit", "-s")

    assert checker.main(["base..HEAD"]) == 0
