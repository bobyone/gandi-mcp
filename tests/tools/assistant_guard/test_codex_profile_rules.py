# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""The committed Codex profile must match the rules derived from the shared guard policy."""

import tomllib
from pathlib import Path

from tools.assistant_guard import codex_profile
from tools.assistant_guard.policy import (
    ALLOWED_EXAMPLE_PATTERNS,
    PROTECTED_DIRECTORIES,
    PROTECTED_FILE_PATTERNS,
)

PROFILE_FILE = Path(__file__).resolve().parents[3] / ".codex" / "config.toml"


def load_profile() -> dict[str, object]:
    with PROFILE_FILE.open("rb") as stream:
        return tomllib.load(stream)


def test_committed_profile_matches_the_policy() -> None:
    configuration = load_profile()
    profile = configuration["permissions"][codex_profile.PROFILE_NAME]  # type: ignore[index]

    assert configuration["default_permissions"] == codex_profile.PROFILE_NAME
    assert profile["filesystem"][":workspace_roots"] == codex_profile.workspace_rules(), (
        "regenerate with: uv run python -m tools.assistant_guard.codex_profile"
    )


def test_samples_agree_with_the_policy() -> None:
    assert codex_profile.check_samples() == []


def test_every_pattern_has_a_sample() -> None:
    assert len(codex_profile.protected_samples()) == len(PROTECTED_FILE_PATTERNS) + len(
        PROTECTED_DIRECTORIES
    )
    assert set(codex_profile.EXAMPLE_NAMES) == set(ALLOWED_EXAMPLE_PATTERNS)


def test_render_workspace_roots_is_valid_toml() -> None:
    rendered = tomllib.loads(codex_profile.render_workspace_roots())

    table = rendered["permissions"][codex_profile.PROFILE_NAME]["filesystem"][":workspace_roots"]
    assert table == codex_profile.workspace_rules()
