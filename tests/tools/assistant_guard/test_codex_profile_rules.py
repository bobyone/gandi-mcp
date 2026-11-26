# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The committed Codex profile must match the rules derived from the shared guard policy."""

import tomllib
from pathlib import Path
from typing import Any

import pytest

from tools.assistant_guard import codex_profile
from tools.assistant_guard.policy import (
    ALLOWED_EXAMPLE_PATTERNS,
    PROTECTED_DIRECTORIES,
    PROTECTED_FILE_PATTERNS,
)

ROOT = Path(__file__).resolve().parents[3]
PROFILE_FILE = ROOT / ".codex" / "config.toml"


def load_profile() -> dict[str, Any]:
    with PROFILE_FILE.open("rb") as stream:
        return tomllib.load(stream)


def test_committed_profile_matches_the_policy() -> None:
    configuration = load_profile()
    profile = configuration["permissions"][codex_profile.PROFILE_NAME]

    assert configuration["default_permissions"] == codex_profile.PROFILE_NAME
    assert profile["filesystem"][":workspace_roots"] == codex_profile.repository_rules(ROOT), (
        "regenerate with: uv run python -m tools.assistant_guard.codex_profile"
    )


def test_globs_only_deny() -> None:
    """Codex rejects any access other than deny on a glob."""
    rules = codex_profile.workspace_rules(codex_profile.example_samples())

    assert all(access == "deny" for path, access in rules.items() if "*" in path)


@pytest.mark.parametrize(
    ("path", "covered"),
    [
        (".env.example", True),
        ("sub/.ENV.PROD", True),
        (".ssh/config", True),
        ("gandi-mcp.example.toml", False),
        ("README.md", False),
    ],
)
def test_is_covered_by_deny_rule(path: str, covered: bool) -> None:
    assert codex_profile.is_covered_by_deny_rule(path) is covered


def test_colliding_examples_keep_only_allowed_covered_paths() -> None:
    paths = [".env", ".env.example", "sub/id_rsa.pub", "README.md", "gandi-mcp.example.toml"]

    assert codex_profile.colliding_examples(paths) == [".env.example", "sub/id_rsa.pub"]


def test_examples_get_exact_write_entries() -> None:
    rules = codex_profile.workspace_rules([".env.example"])

    assert rules[".env.example"] == "write"
    assert rules["**/.env.*"] == "deny"


def test_samples_agree_with_the_policy() -> None:
    assert codex_profile.check_samples() == []


def test_every_pattern_has_a_sample() -> None:
    assert len(codex_profile.protected_samples()) == len(PROTECTED_FILE_PATTERNS) + len(
        PROTECTED_DIRECTORIES
    )
    assert set(codex_profile.EXAMPLE_NAMES) == set(ALLOWED_EXAMPLE_PATTERNS)


def test_rendered_table_is_valid_toml() -> None:
    rules = codex_profile.workspace_rules([".env.example"])
    rendered = tomllib.loads(codex_profile.render_workspace_roots(rules))

    profile = rendered["permissions"][codex_profile.PROFILE_NAME]
    assert profile["filesystem"][":workspace_roots"] == rules
