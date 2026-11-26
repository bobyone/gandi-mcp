# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the npm license check."""

import json
from pathlib import Path

from scripts import check_npm_licenses as check

LOCK = {
    "packages": {
        "": {"name": "gandi-mcp-ui", "license": "GPL-2.0-or-later"},
        "node_modules/react": {"version": "19.3.1", "license": "MIT"},
        "node_modules/a/node_modules/b": {"version": "1.0.0", "license": "(MIT OR GPL-3.0)"},
        "node_modules/vite": {"version": "8.4.0", "license": "MIT", "dev": True},
        "node_modules/typescript": {
            "version": "6.0.3",
            "license": "Apache-2.0",
            "devOptional": True,
        },
    }
}


def test_lists_runtime_packages_only() -> None:
    assert check.runtime_packages(LOCK) == {"react@19.3.1": "MIT", "b@1.0.0": "(MIT OR GPL-3.0)"}


def test_reports_missing_unsupported_and_incompatible_licenses() -> None:
    violations = check.find_violations(
        {"a@1": None, "b@1": "MIT AND", "c@1": "SSPL-1.0", "d@1": "MIT"}
    )

    assert violations == [
        "a@1: no license declared",
        "b@1: unsupported license expression (unexpected end of expression)",
        "c@1: incompatible license SSPL-1.0",
    ]


def test_main_on_a_lock_file(tmp_path: Path) -> None:
    lock = tmp_path / "package-lock.json"
    lock.write_text(json.dumps(LOCK), encoding="utf-8")

    assert check.main(["--lock", str(lock)]) == 0

    lock.write_text(
        json.dumps({"packages": {"node_modules/x": {"version": "1", "license": 3}}}),
        encoding="utf-8",
    )
    assert check.main(["--lock", str(lock)]) == 1


def test_the_real_lock_file_is_compatible() -> None:
    root = Path(__file__).resolve().parents[2]

    assert check.main(["--lock", str(root / "ui" / "package-lock.json")]) == 0
