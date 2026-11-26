# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that every commit of a range carries a DCO sign-off matching its author.

Usage: ``python scripts/check_dco.py <base>..<head>``.
"""

import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass

SIGN_OFF = re.compile(r"^Signed-off-by: .+ <(?P<email>[^>]+)>\s*$", re.M)
FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"

logger = logging.getLogger("check_dco")


@dataclass(frozen=True)
class Commit:
    """A commit as needed by the check."""

    sha: str
    author_email: str
    message: str


def is_signed_off(commit: Commit) -> bool:
    """Tell whether the commit is signed off by its author."""
    emails = {match["email"].lower() for match in SIGN_OFF.finditer(commit.message)}
    return commit.author_email.lower() in emails


def read_commits(revision_range: str) -> list[Commit]:
    """Read the non-merge commits of a range with Git."""
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git is required")
    output = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [
            git,
            "log",
            "--no-merges",
            f"--format=%H{FIELD_SEPARATOR}%ae{FIELD_SEPARATOR}%B{RECORD_SEPARATOR}",
            revision_range,
            "--",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    commits = []
    for record in output.split(RECORD_SEPARATOR):
        if record.strip():
            sha, email, message = record.strip("\n").split(FIELD_SEPARATOR, 2)
            commits.append(Commit(sha=sha, author_email=email, message=message))
    return commits


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1 or arguments[0].startswith("-"):
        logger.error("usage: check_dco.py <base>..<head>")
        return 2
    commits = read_commits(arguments[0])
    unsigned = [commit for commit in commits if not is_signed_off(commit)]
    for commit in unsigned:
        logger.error(
            "commit %s lacks a 'Signed-off-by' matching its author; amend it with "
            "'git commit --amend -s' or 'git rebase --signoff'",
            commit.sha[:12],
        )
    logger.info("%d commits checked", len(commits))
    return 1 if unsigned else 0


if __name__ == "__main__":
    sys.exit(main())
