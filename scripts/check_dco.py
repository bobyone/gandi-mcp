# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that every commit of a range, merges included, is signed off by its author.

Only the ``Signed-off-by`` trailers parsed by Git count: a matching line elsewhere
in the message body does not.

Usage: ``python scripts/check_dco.py <base>..<head>``.
"""

import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass

FIELD_SEPARATOR = "\x1f"
RECORD_SEPARATOR = "\x1e"
TRAILER_SEPARATOR = "\x1d"
LOG_FORMAT = (
    f"%H{FIELD_SEPARATOR}%ae{FIELD_SEPARATOR}"
    "%(trailers:key=Signed-off-by,valueonly,separator=%x1d)"
    f"{RECORD_SEPARATOR}"
)
IDENTITY = re.compile(r"^.+ <(?P<email>[^<>\s]+)>$")

logger = logging.getLogger("check_dco")


@dataclass(frozen=True)
class Commit:
    """A commit as needed by the check."""

    sha: str
    author_email: str
    sign_offs: tuple[str, ...]


def is_signed_off(commit: Commit) -> bool:
    """Tell whether one of the commit's sign-off trailers names its author."""
    emails = {
        match["email"].lower()
        for sign_off in commit.sign_offs
        if (match := IDENTITY.match(sign_off.strip()))
    }
    return commit.author_email.lower() in emails


def parse_log(output: str) -> list[Commit]:
    """Parse the output of ``git log --format=LOG_FORMAT``."""
    commits = []
    for record in output.split(RECORD_SEPARATOR):
        if not record.strip():
            continue
        sha, email, trailers = record.strip("\n").split(FIELD_SEPARATOR, 2)
        sign_offs = tuple(value for value in trailers.split(TRAILER_SEPARATOR) if value.strip())
        commits.append(Commit(sha=sha, author_email=email, sign_offs=sign_offs))
    return commits


def read_commits(revision_range: str) -> list[Commit]:
    """Read every commit of a range, merge commits included."""
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git is required")
    output = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [git, "log", f"--format={LOG_FORMAT}", revision_range, "--"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return parse_log(output)


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
            "commit %s lacks a 'Signed-off-by' trailer matching its author; amend it with "
            "'git commit --amend -s', 'git rebase --signoff' or 'git merge --signoff'",
            commit.sha[:12],
        )
    logger.info("%d commits checked", len(commits))
    return 1 if unsigned else 0


if __name__ == "__main__":
    sys.exit(main())
