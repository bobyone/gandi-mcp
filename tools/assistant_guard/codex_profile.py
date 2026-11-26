# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Derive the Codex sandbox filesystem rules from the shared guard policy.

Each protected pattern of the policy becomes a ``deny`` glob. Codex cannot re-allow a
file covered by a deny glob: globs only support ``deny``, and exact-path entries apply to
directories. An example covered by a deny glob (for example ``.env.example`` under
``**/.env.*``) is therefore unreadable in the Codex sandbox, while the hook allows it. The
repository avoids this: no tracked example may be covered by a deny glob
(:func:`colliding_examples`), and its examples use distinct names such as
``gandi-mcp.example.toml``.

The workspace rules of the ``gandi-mcp`` profile in ``.codex/config.toml`` must equal
:func:`workspace_rules`; a test enforces it. Print the expected TOML table with
``python -m tools.assistant_guard.codex_profile``.
"""

import shutil
import subprocess
import sys
from collections.abc import Iterable
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath

from tools.assistant_guard.policy import (
    ALLOWED_EXAMPLE_PATTERNS,
    PROTECTED_DIRECTORIES,
    PROTECTED_FILE_PATTERNS,
    is_protected_path,
)

PROFILE_NAME = "gandi-mcp"
SAMPLE_STEM = "prod"
# One example name per allowed pattern, not covered by any deny glob.
EXAMPLE_NAMES: dict[str, str] = {
    "*.example": "settings.example",
    "*.example.*": "gandi-mcp.example.toml",
    "*.sample": "settings.sample",
    "*.template": "message.template",
    "*.pub": "signing.pub",
}
# One example name per allowed pattern, covered by a deny glob: unreadable under Codex.
COVERED_EXAMPLE_NAMES: dict[str, str] = {
    "*.example": ".env.example",
    "*.example.*": "credentials.example.json",
    "*.sample": ".env.sample",
    "*.template": ".env.template",
    "*.pub": "id_ed25519.pub",
}


def deny_rules() -> dict[str, str]:
    """Return one ``deny`` glob per protected file pattern and directory."""
    rules = {f"**/{pattern}": "deny" for pattern in PROTECTED_FILE_PATTERNS}
    rules.update({f"**/{directory}": "deny" for directory in PROTECTED_DIRECTORIES})
    return rules


def is_covered_by_deny_rule(path: str) -> bool:
    """Tell whether a deny glob covers a relative path, ignoring the example exemptions."""
    parts = [part.lower() for part in PurePosixPath(path).parts]
    if any(part in PROTECTED_DIRECTORIES for part in parts[:-1]):
        return True
    return any(fnmatchcase(parts[-1], pattern) for pattern in PROTECTED_FILE_PATTERNS)


def colliding_examples(paths: Iterable[str]) -> list[str]:
    """Return the allowed paths that a deny glob would nevertheless cover."""
    return sorted(
        {path for path in paths if is_covered_by_deny_rule(path) and not is_protected_path(path)}
    )


def workspace_rules() -> dict[str, str]:
    """Return the ``:workspace_roots`` table: the workspace is writable, protected paths denied."""
    return {".": "write", **deny_rules()}


def tracked_files(root: Path) -> list[str]:
    """List the files tracked by Git under a repository root, as POSIX relative paths."""
    git = shutil.which("git")
    if git is None:
        raise SystemExit("git is required")
    output = subprocess.run(  # noqa: S603 - fixed arguments, no shell
        [git, "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    return [path for path in output.split("\0") if path]


def render_workspace_roots(rules: dict[str, str]) -> str:
    """Render a ``:workspace_roots`` table as TOML."""
    lines = [f'[permissions.{PROFILE_NAME}.filesystem.":workspace_roots"]']
    lines += [f'"{path}" = "{access}"' for path, access in rules.items()]
    return "\n".join(lines) + "\n"


def protected_samples() -> list[str]:
    """Return one synthetic relative path per protected pattern and directory."""
    samples = [pattern.replace("*", SAMPLE_STEM) for pattern in PROTECTED_FILE_PATTERNS]
    samples += [f"{directory}/config" for directory in PROTECTED_DIRECTORIES]
    return samples


def example_samples() -> list[str]:
    """Return one synthetic example path per allowed pattern, not covered by a deny glob."""
    return [EXAMPLE_NAMES[pattern] for pattern in ALLOWED_EXAMPLE_PATTERNS]


def covered_example_samples() -> list[str]:
    """Return one synthetic example path per allowed pattern, covered by a deny glob."""
    return [COVERED_EXAMPLE_NAMES[pattern] for pattern in ALLOWED_EXAMPLE_PATTERNS]


def check_samples() -> list[str]:
    """Return inconsistencies between the samples and the policy (expected: none)."""
    errors = [
        f"{name} should be protected" for name in protected_samples() if not is_protected_path(name)
    ]
    errors += [
        f"{name} should be an allowed example not covered by a deny glob"
        for name in example_samples()
        if is_protected_path(name) or colliding_examples([name])
    ]
    errors += [
        f"{name} should be an allowed example covered by a deny glob"
        for name in covered_example_samples()
        if name not in colliding_examples([name])
    ]
    return errors


if __name__ == "__main__":
    sys.stdout.write(render_workspace_roots(workspace_rules()))
