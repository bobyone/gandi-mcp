# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that every runtime npm package of the MCP App has a GPL-compatible license.

Runtime packages are those of ``ui/package-lock.json`` not marked ``dev``: they may be
bundled in ``app.html``. Development tools are not distributed and are not checked.
License expressions are evaluated as in ``scripts/check_licenses.py``.

Usage: ``python scripts/check_npm_licenses.py [--lock FILE]``.
"""

import argparse
import json
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from scripts.check_licenses import UnsupportedExpressionError, is_allowed

DEFAULT_LOCK = Path("ui/package-lock.json")

logger = logging.getLogger("check_npm_licenses")


def runtime_packages(lock: Mapping[str, Any]) -> dict[str, str | None]:
    """Return the license of every runtime package, keyed by ``name@version``."""
    packages = lock.get("packages", {})
    result: dict[str, str | None] = {}
    for path, info in packages.items():
        if not path or info.get("dev") or info.get("devOptional"):
            continue
        name = path.rsplit("node_modules/", 1)[-1]
        license_ = info.get("license")
        result[f"{name}@{info.get('version', '?')}"] = (
            license_ if isinstance(license_, str) else None
        )
    return result


def find_violations(packages: Mapping[str, str | None]) -> list[str]:
    """Return one message per package without an allowed license."""
    violations = []
    for package, expression in sorted(packages.items()):
        if expression is None:
            violations.append(f"{package}: no license declared")
            continue
        try:
            allowed = is_allowed(expression)
        except UnsupportedExpressionError as error:
            violations.append(f"{package}: unsupported license expression ({error})")
            continue
        if not allowed:
            violations.append(f"{package}: incompatible license {expression}")
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    arguments = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    lock = json.loads(arguments.lock.read_text(encoding="utf-8"))
    packages = runtime_packages(lock)
    violations = find_violations(packages)
    for violation in violations:
        logger.error("%s", violation)
    logger.info("%d runtime npm packages checked", len(packages))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
