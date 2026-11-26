# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that every runtime dependency has a license compatible with GPL-2.0-or-later.

Apache-2.0 dependencies are accepted because the project is distributed under
"GPL-2.0-or-later", which allows combining them under the terms of GPL-3.0.

License expressions follow SPDX precedence: ``WITH`` binds tightest, then ``AND``,
then ``OR``; parentheses group. Several classifiers reported together (``A; B``)
must all be allowed. Unsupported expressions are rejected.

Dependencies restricted to other platforms by an environment marker are skipped:
run the check on every supported platform (the CI does).

Usage: ``uv run python scripts/check_licenses.py``.
"""

import json
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass

ALLOWED_LICENSES = frozenset(
    {
        "0BSD",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "CC0-1.0",
        "GPL-2.0-or-later",
        "GPL-3.0-or-later",
        "ISC",
        "LGPL-2.1-or-later",
        "LGPL-3.0-or-later",
        "MIT",
        "MIT-0",
        "MPL-2.0",
        "PSF-2.0",
        "Unlicense",
        "Zlib",
    }
)
ALIASES = {
    "apache software license": "Apache-2.0",
    "bsd license": "BSD-3-Clause",
    "mit license": "MIT",
    "python software foundation license": "PSF-2.0",
    "isc license (iscl)": "ISC",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
}
TOKEN_SEPARATOR = re.compile(r"(\(|\)|\bAND\b|\bOR\b|\bWITH\b)")
OPERATORS = frozenset({"AND", "OR", "WITH"})

logger = logging.getLogger("check_licenses")


class UnsupportedExpressionError(ValueError):
    """Raised when a license expression cannot be parsed."""


@dataclass(frozen=True)
class Requirement:
    """A runtime dependency from the lock file."""

    name: str
    platform_specific: bool


def canonical_name(name: str) -> str:
    """Normalize a distribution name (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def normalize(name: str) -> str:
    """Map a license name reported by package metadata to an SPDX identifier."""
    cleaned = name.strip()
    return ALIASES.get(cleaned.lower(), cleaned)


def tokenize(expression: str) -> list[str]:
    """Split an expression into parentheses, operators and license operands."""
    tokens = [token.strip() for token in TOKEN_SEPARATOR.split(expression)]
    return [token for token in tokens if token]


class _Parser:
    """Recursive descent evaluation of an SPDX expression against the allowed licenses."""

    def __init__(self, tokens: list[str]) -> None:
        self.tokens = tokens
        self.position = 0

    def peek(self) -> str | None:
        return self.tokens[self.position] if self.position < len(self.tokens) else None

    def take(self) -> str:
        token = self.peek()
        if token is None:
            raise UnsupportedExpressionError("unexpected end of expression")
        self.position += 1
        return token

    def parse(self) -> bool:
        result = self.disjunction()
        if self.peek() is not None:
            raise UnsupportedExpressionError("unexpected trailing tokens")
        return result

    def disjunction(self) -> bool:
        results = [self.conjunction()]
        while self.peek() == "OR":
            self.take()
            results.append(self.conjunction())
        return any(results)

    def conjunction(self) -> bool:
        results = [self.term()]
        while self.peek() == "AND":
            self.take()
            results.append(self.term())
        return all(results)

    def term(self) -> bool:
        symbol = self.take()
        if symbol == "(":
            result = self.disjunction()
            if self.take() != ")":
                raise UnsupportedExpressionError("missing closing parenthesis")
            return result
        if symbol in OPERATORS or symbol == ")":
            raise UnsupportedExpressionError("operand expected")
        if self.peek() == "WITH":
            self.take()
            exception = self.take()
            if exception in OPERATORS or exception in {"(", ")"}:
                raise UnsupportedExpressionError("exception identifier expected")
        return normalize(symbol) in ALLOWED_LICENSES


def is_allowed(expression: str) -> bool:
    """Tell whether a license expression only requires allowed licenses.

    Raises:
        UnsupportedExpressionError: if the expression cannot be parsed.
    """
    classifiers = [part for part in expression.split(";") if part.strip()]
    if not classifiers:
        raise UnsupportedExpressionError("empty expression")
    return all(_Parser(tokenize(classifier)).parse() for classifier in classifiers)


def parse_requirements(exported: str) -> list[Requirement]:
    """Parse ``uv export`` output into requirements, flagging platform-specific ones."""
    requirements = []
    for line in exported.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        specifier, _, marker = line.partition(";")
        name = specifier.split("==")[0].strip()
        requirements.append(
            Requirement(canonical_name(name), platform_specific=bool(marker.strip()))
        )
    return requirements


def runtime_requirements() -> list[Requirement]:
    """List runtime dependencies for every platform from the lock file."""
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is required: https://docs.astral.sh/uv/")
    exported = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [
            uv,
            "export",
            "--no-dev",
            "--no-hashes",
            "--no-emit-project",
            "--no-header",
            "--no-annotate",
            "--format",
            "requirements.txt",
            "--all-extras",
            "--locked",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return parse_requirements(exported)


def installed_licenses(packages: Iterable[str]) -> dict[str, str]:
    """Return the license of each installed package, keyed by canonical name."""
    report = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [
            sys.executable,
            "-m",
            "piplicenses",
            "--from=mixed",
            "--format=json",
            "--packages",
            *packages,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return {canonical_name(entry["Name"]): entry["License"] for entry in json.loads(report)}


def find_violations(requirements: list[Requirement], licenses: dict[str, str]) -> list[str]:
    """Return one message per dependency that is missing or not allowed."""
    violations = []
    for requirement in requirements:
        expression = licenses.get(requirement.name)
        if expression is None:
            if requirement.platform_specific:
                logger.info("%s targets another platform: skipped here", requirement.name)
            else:
                violations.append(f"{requirement.name}: not installed, license not checked")
            continue
        try:
            allowed = is_allowed(expression)
        except UnsupportedExpressionError as error:
            violations.append(f"{requirement.name}: unsupported license expression ({error})")
            continue
        if not allowed:
            violations.append(f"{requirement.name}: incompatible license {expression}")
    return violations


def main() -> int:
    """Command line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    requirements = runtime_requirements()
    licenses = installed_licenses(requirement.name for requirement in requirements)
    violations = find_violations(requirements, licenses)
    for violation in violations:
        logger.error("%s", violation)
    logger.info("%d runtime dependencies checked on this platform", len(licenses))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
