# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Check that every runtime dependency has a license compatible with GPL-2.0-or-later.

Apache-2.0 dependencies are accepted because the project is distributed under
"GPL-2.0-or-later", which allows combining them under the terms of GPL-3.0.

Usage: ``uv run python scripts/check_licenses.py``.
"""

import json
import logging
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable

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
OPERATOR = re.compile(r"\s+(OR|AND)\s+")

logger = logging.getLogger("check_licenses")


def normalize(name: str) -> str:
    """Map a license name reported by package metadata to an SPDX identifier."""
    cleaned = name.strip().strip("()")
    return ALIASES.get(cleaned.lower(), cleaned)


def is_allowed(expression: str) -> bool:
    """Evaluate a simple SPDX expression (``A OR B``, ``A AND B``, ``A; B`` classifiers)."""
    if ";" in expression:
        return any(is_allowed(part) for part in expression.split(";"))
    parts = OPERATOR.split(expression.strip())
    licenses = [normalize(part) for part in parts[::2]]
    operators = set(parts[1::2])
    if "OR" in operators:
        return any(license_id in ALLOWED_LICENSES for license_id in licenses)
    return all(license_id in ALLOWED_LICENSES for license_id in licenses)


def runtime_packages() -> list[str]:
    """List runtime dependency names from the lock file."""
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
    return [line.split("==")[0].split(";")[0].strip() for line in exported.splitlines() if line]


def installed_licenses(packages: Iterable[str]) -> dict[str, str]:
    """Return the license of each installed package, as reported by pip-licenses."""
    report = subprocess.run(  # noqa: S603
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
    return {entry["Name"]: entry["License"] for entry in json.loads(report)}


def find_violations(licenses: dict[str, str]) -> list[str]:
    """Return the packages whose license is not allowed."""
    return sorted(name for name, expression in licenses.items() if not is_allowed(expression))


def main() -> int:
    """Command line entry point."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s", stream=sys.stderr)
    licenses = installed_licenses(runtime_packages())
    violations = find_violations(licenses)
    for name in violations:
        logger.error("incompatible or unknown license for %s: %s", name, licenses[name])
    logger.info("%d runtime dependencies checked", len(licenses))
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
