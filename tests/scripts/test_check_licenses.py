# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Tests of the dependency license checker."""

import pytest

from scripts import check_licenses as checker


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
        ("Proprietary; MIT License", True),
        ("AGPL-3.0-only", False),
    ],
)
def test_is_allowed(expression: str, allowed: bool) -> None:
    assert checker.is_allowed(expression) is allowed


def test_find_violations() -> None:
    assert checker.find_violations({"good": "MIT", "bad": "SSPL-1.0"}) == ["bad"]


def test_runtime_dependencies_are_compatible() -> None:
    """Integration test on the real lock file and environment."""
    assert checker.main() == 0
