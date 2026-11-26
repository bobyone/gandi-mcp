# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Integration test of the committed Codex permission profile, enforced by ``codex sandbox``.

Synthetic protected files and their examples are created in a temporary repository; the
profile read from ``.codex/config.toml`` must deny the former and allow the latter.
Skipped when the Codex CLI or its sandbox is not available (set ``CODEX_CLI`` to its path
if it is not on the ``PATH``). With ``CODEX_PROFILE_REQUIRED=1`` (CI), an unavailable sandbox
fails the test instead.
"""

import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROFILE_FILE = ROOT / ".codex" / "config.toml"
CODEX = os.environ.get("CODEX_CLI") or shutil.which("codex")
REQUIRED = os.environ.get("CODEX_PROFILE_REQUIRED") == "1"
# Sandbox start-up failures: a read failing for these reasons proves nothing.
SANDBOX_UNAVAILABLE = ("sandbox failed", "bwrap:")

pytestmark = pytest.mark.skipif(CODEX is None and not REQUIRED, reason="Codex CLI not available")

DENIED = [".env", "gandi-mcp.toml", "sub/Gandi-MCP.TOML", "sub/.env.local", "server.pem"]
ALLOWED = ["README.md", ".env.example", "gandi-mcp.example.toml", "sub/notes.txt"]


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
    return [
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
    if any(marker in result.stderr for marker in SANDBOX_UNAVAILABLE):
        message = "Codex sandbox unavailable: " + result.stderr.strip().splitlines()[-1]
        if REQUIRED:
            pytest.fail(message)
        pytest.skip(message)
    return result


@pytest.fixture(scope="module")
def repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("codex-profile")
    subprocess.run([shutil.which("git") or "git", "init", "-q", str(path)], check=True)  # noqa: S603
    for relative in DENIED + ALLOWED:
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
