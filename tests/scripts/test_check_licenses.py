# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the dependency license checker."""

import pytest

from scripts import check_licenses as checker
from scripts.check_licenses import Requirement, UnsupportedExpressionError


@pytest.mark.parametrize(
    ("expression", "allowed"),
    [
        ("MIT", True),
        ("MIT License", True),
        ("BSD License", True),
        ("Apache-2.0 OR BSD-3-Clause", True),
        ("GPL-3.0-only OR MIT", True),
        ("MIT AND Apache-2.0", True),
        ("MIT AND SSPL-1.0", False),
        ("Python Software Foundation License", True),
        ("UNKNOWN", False),
        ("AGPL-3.0-only", False),
        # AND binds tighter than OR: every branch requires SSPL here.
        ("MIT AND SSPL-1.0 OR Apache-2.0 AND SSPL-1.0", False),
        ("SSPL-1.0 AND MIT OR SSPL-1.0", False),
        ("(MIT OR SSPL-1.0) AND Apache-2.0", True),
        ("(MIT OR SSPL-1.0) AND SSPL-1.0", False),
        ("MIT OR (SSPL-1.0 AND Apache-2.0)", True),
        ("GPL-2.0-or-later WITH Classpath-exception-2.0", True),
        ("Apache-2.0 WITH LLVM-exception OR SSPL-1.0", True),
        ("(GPL-2.0-or-later WITH Classpath-exception-2.0) AND MIT", True),
        ("Proprietary; MIT License", False),
        ("MIT License; BSD License", True),
    ],
)
def test_is_allowed(expression: str, allowed: bool) -> None:
    assert checker.is_allowed(expression) is allowed


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "MIT AND",
        "(MIT OR Apache-2.0",
        "MIT )",
        "OR MIT",
        "MIT WITH",
        "MIT WITH (",
        "( )",
        # Unreviewed exceptions fail closed, even on an allowed license.
        "MIT WITH Unknown-exception",
        "Apache-2.0 WITH Classpath-exception-2.0",
        "GPL-2.0-or-later WITH Unknown-exception OR MIT",
    ],
)
def test_unsupported_expressions_are_rejected(expression: str) -> None:
    with pytest.raises(UnsupportedExpressionError):
        checker.is_allowed(expression)


def test_parse_requirements_flags_platform_markers() -> None:
    exported = "anyio==4.0\nPyWin32==311 ; sys_platform == 'win32'\n# comment\n\n"

    assert checker.parse_requirements(exported) == [
        Requirement("anyio", platform_specific=False),
        Requirement("pywin32", platform_specific=True),
    ]


def test_find_violations() -> None:
    requirements = [
        Requirement("good", platform_specific=False),
        Requirement("bad", platform_specific=False),
        Requirement("odd", platform_specific=False),
        Requirement("absent", platform_specific=False),
        Requirement("windows-only", platform_specific=True),
    ]
    licenses = {"good": "MIT", "bad": "SSPL-1.0", "odd": "MIT AND"}

    assert checker.find_violations(requirements, licenses) == [
        "bad: incompatible license SSPL-1.0",
        "odd: unsupported license expression (unexpected end of expression)",
        "absent: not installed, license not checked",
    ]


def test_runtime_dependencies_are_compatible() -> None:
    """Integration test on the real lock file and environment."""
    assert checker.main() == 0
