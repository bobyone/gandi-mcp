# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Derive the Codex sandbox filesystem rules from the shared guard policy.

The workspace rules of the ``gandi-mcp`` profile in ``.codex/config.toml`` must equal
:func:`workspace_rules`; a test enforces it. Print the expected TOML table with
``python -m tools.assistant_guard.codex_profile``.
"""

import sys

from tools.assistant_guard.policy import (
    ALLOWED_EXAMPLE_PATTERNS,
    PROTECTED_DIRECTORIES,
    PROTECTED_FILE_PATTERNS,
    is_protected_path,
)

PROFILE_NAME = "gandi-mcp"
SAMPLE_STEM = "prod"
# One example name per allowed pattern, each also matching a protected pattern.
EXAMPLE_NAMES: dict[str, str] = {
    "*.example": ".env.example",
    "*.example.*": "gandi-mcp.example.toml",
    "*.sample": "secrets.env.sample",
    "*.template": ".env.template",
    "*.pub": "id_ed25519.pub",
}


def workspace_rules() -> dict[str, str]:
    """Return the ``:workspace_roots`` table: writable, protected paths denied, examples kept."""
    rules = {".": "write"}
    rules.update({f"**/{pattern}": "deny" for pattern in PROTECTED_FILE_PATTERNS})
    rules.update({f"**/{directory}": "deny" for directory in PROTECTED_DIRECTORIES})
    rules.update({f"**/{pattern}": "write" for pattern in ALLOWED_EXAMPLE_PATTERNS})
    return rules


def protected_samples() -> list[str]:
    """Return one synthetic relative path per protected pattern and directory."""
    samples = [pattern.replace("*", SAMPLE_STEM) for pattern in PROTECTED_FILE_PATTERNS]
    samples += [f"{directory}/config" for directory in PROTECTED_DIRECTORIES]
    return samples


def example_samples() -> list[str]:
    """Return one synthetic relative path per allowed example pattern."""
    return [EXAMPLE_NAMES[pattern] for pattern in ALLOWED_EXAMPLE_PATTERNS]


def render_workspace_roots() -> str:
    """Render the expected TOML table of the profile's workspace rules."""
    lines = [f'[permissions.{PROFILE_NAME}.filesystem.":workspace_roots"]']
    lines += [f'"{path}" = "{access}"' for path, access in workspace_rules().items()]
    return "\n".join(lines) + "\n"


def check_samples() -> list[str]:
    """Return inconsistencies between the samples and the policy (expected: none)."""
    errors = [
        f"{name} should be protected" for name in protected_samples() if not is_protected_path(name)
    ]
    errors += [f"{name} should be allowed" for name in example_samples() if is_protected_path(name)]
    return errors


if __name__ == "__main__":
    sys.stdout.write(render_workspace_roots())
