# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration test of the committed Codex permission profile, enforced by ``codex sandbox``.

Synthetic protected files and examples are created in a temporary repository, and the
profile read from ``.codex/config.toml`` is applied. It must deny every protected pattern and
allow examples that no deny glob covers. Examples covered by a deny glob are denied: Codex
cannot re-allow them (see ``tools/assistant_guard/codex_profile.py``).
Skipped when the Codex CLI or its sandbox is not available (set ``CODEX_CLI`` to its path
if it is not on the ``PATH``). With ``CODEX_PROFILE_REQUIRED=1`` (CI), an unavailable sandbox
fails the test instead.

On Windows, deny-read rules need the elevated sandbox backend: set
``CODEX_WINDOWS_SANDBOX=elevated`` (it requires administrator rights the first time, to
install the backend). It is not enabled by default, so that running the tests never asks
for elevation.
"""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from tools.assistant_guard.codex_profile import (
    covered_example_samples,
    example_samples,
    protected_samples,
)

ROOT = Path(__file__).resolve().parents[3]
PROFILE_FILE = ROOT / ".codex" / "config.toml"
CODEX = os.environ.get("CODEX_CLI") or shutil.which("codex")
REQUIRED = os.environ.get("CODEX_PROFILE_REQUIRED") == "1"
WINDOWS_SANDBOX = os.environ.get("CODEX_WINDOWS_SANDBOX")
WINDOWS_SANDBOX_MODES = frozenset({"elevated", "unelevated"})
# Sandbox start-up failures: a read failing for these reasons proves nothing.
SANDBOX_UNAVAILABLE = ("sandbox failed", "bwrap:")
# Codex rejects an invalid configuration: every read fails, which must never pass a test.
CONFIGURATION_ERROR = "Error:"

pytestmark = pytest.mark.skipif(CODEX is None and not REQUIRED, reason="Codex CLI not available")

# One synthetic file per protected pattern of the shared policy, at the root and nested.
DENIED = [*protected_samples(), *(f"sub/{name}" for name in protected_samples())]
# On case-insensitive file systems, a mixed-case name designates the protected file itself.
if sys.platform in {"win32", "darwin"}:
    DENIED.append("sub/Gandi-MCP.TOML")
# Examples covered by a deny glob, which Codex cannot re-allow.
COVERED = [*covered_example_samples(), *(f"sub/{name}" for name in covered_example_samples())]
# One example per allowed pattern, not covered by any deny glob, and ordinary files.
ALLOWED = [
    "README.md",
    "sub/notes.txt",
    *example_samples(),
    *(f"sub/{n}" for n in example_samples()),
]


def inline_toml(value: Any) -> str:
    """Serialize a TOML value (tables, strings, integers, booleans) as inline TOML."""
    if isinstance(value, dict):
        items = ", ".join(
            f"{inline_toml(str(key))} = {inline_toml(item)}" for key, item in value.items()
        )
        return "{" + items + "}"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    raise TypeError(type(value).__name__)


def profile_overrides() -> list[str]:
    with PROFILE_FILE.open("rb") as stream:
        configuration = tomllib.load(stream)
    backend = []
    if WINDOWS_SANDBOX is not None:
        if WINDOWS_SANDBOX not in WINDOWS_SANDBOX_MODES:
            pytest.fail(f"CODEX_WINDOWS_SANDBOX must be one of {sorted(WINDOWS_SANDBOX_MODES)}")
        backend = ["-c", f"windows.sandbox={inline_toml(WINDOWS_SANDBOX)}"]
    return [
        *backend,
        "-c",
        f"default_permissions={inline_toml(configuration['default_permissions'])}",
        "-c",
        f"permissions={inline_toml(configuration['permissions'])}",
    ]


def read_in_sandbox(repository: Path, relative: str) -> subprocess.CompletedProcess[str]:
    path = str(Path(relative))
    reader = ["cmd", "/c", "type", path] if sys.platform == "win32" else ["cat", path]
    if CODEX is None:
        pytest.fail("CODEX_PROFILE_REQUIRED is set but the Codex CLI was not found")
    result = subprocess.run(  # noqa: S603 - test-controlled arguments, no shell
        [CODEX, "sandbox", *profile_overrides(), "--", *reader],
        cwd=repository,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    if result.stderr.lstrip().startswith(CONFIGURATION_ERROR):
        pytest.fail("Codex rejected the profile: " + result.stderr.strip()[-500:])
    if any(marker in result.stderr for marker in SANDBOX_UNAVAILABLE):
        message = "Codex sandbox unavailable: " + result.stderr.strip()[-800:]
        if REQUIRED:
            pytest.fail(message)
        pytest.skip(message)
    return result


@pytest.fixture(scope="module")
def repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("codex-profile")
    subprocess.run([shutil.which("git") or "git", "init", "-q", str(path)], check=True)  # noqa: S603
    for relative in DENIED + COVERED + ALLOWED:
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("synthetic-value\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("relative", DENIED)
def test_profile_denies_protected_files(repository: Path, relative: str) -> None:
    result = read_in_sandbox(repository, relative)

    assert "synthetic-value" not in result.stdout


@pytest.mark.parametrize("relative", ALLOWED)
def test_profile_allows_examples_and_ordinary_files(repository: Path, relative: str) -> None:
    result = read_in_sandbox(repository, relative)

    assert "synthetic-value" in result.stdout, result.stderr[-500:]


@pytest.mark.parametrize("relative", COVERED)
def test_codex_cannot_allow_examples_covered_by_a_deny_glob(
    repository: Path, relative: str
) -> None:
    """Known Codex limitation: if this starts failing, covered examples can be re-allowed."""
    result = read_in_sandbox(repository, relative)

    assert "synthetic-value" not in result.stdout
