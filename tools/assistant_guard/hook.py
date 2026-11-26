# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""PreToolUse hook entry point: ``python tools/assistant_guard/hook.py <claude|codex>``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.assistant_guard.adapters import (
    EVALUATORS,
    evaluate_hook_input,
    render_decision,
)


def run(argv: list[str], stdin: str) -> str:
    """Return the hook's stdout for the given client and input."""
    if len(argv) != 1 or argv[0] not in EVALUATORS:
        raise SystemExit("usage: hook.py <claude|codex>")
    return render_decision(evaluate_hook_input(argv[0], stdin))


if __name__ == "__main__":
    sys.stdout.write(run(sys.argv[1:], sys.stdin.read()))
