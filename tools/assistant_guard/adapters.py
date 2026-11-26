# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Translate each assistant client's PreToolUse hook input into policy checks."""

import json
import re
import shlex
from collections.abc import Callable
from typing import Any

from tools.assistant_guard.policy import (
    ALLOW,
    MALFORMED_REASON,
    Decision,
    check_command,
    check_path,
)

FILE_TOOLS = {
    "Read": "file_path",
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}
SEARCH_TOOLS = frozenset({"Grep"})
SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
PATCH_FILE_LINE = re.compile(
    r"^\*\*\* (?:Add|Update|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.M
)


def _first_denial(decisions: list[Decision]) -> Decision:
    return next((decision for decision in decisions if not decision.allowed), ALLOW)


def _shell_command(value: object) -> object:
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return shlex.join(value)
    return value


def evaluate_claude(tool_name: str, tool_input: dict[str, Any]) -> Decision:
    """Evaluate a Claude Code tool call."""
    if tool_name in FILE_TOOLS:
        return check_path(tool_input.get(FILE_TOOLS[tool_name]))
    if tool_name in SEARCH_TOOLS:
        return _first_denial(
            [check_path(tool_input[key]) for key in ("path", "glob") if key in tool_input]
        )
    if tool_name in SHELL_TOOLS:
        return check_command(tool_input.get("command"))
    return ALLOW


def evaluate_codex(tool_name: str, tool_input: dict[str, Any]) -> Decision:
    """Evaluate a Codex tool call (shell commands and patches)."""
    command = _shell_command(tool_input.get("command"))
    if tool_name == "apply_patch":
        if not isinstance(command, str):
            return Decision(allowed=False, reason=MALFORMED_REASON)
        paths = [first or second for first, second in PATCH_FILE_LINE.findall(command)]
        return _first_denial([check_path(path.strip()) for path in paths])
    if tool_name in SHELL_TOOLS:
        return check_command(command)
    return ALLOW


EVALUATORS: dict[str, Callable[[str, dict[str, Any]], Decision]] = {
    "claude": evaluate_claude,
    "codex": evaluate_codex,
}


def evaluate_hook_input(client: str, raw_input: str) -> Decision:
    """Parse a hook's stdin and evaluate it; malformed input is denied without being echoed."""
    try:
        payload = json.loads(raw_input)
    except ValueError:
        return Decision(allowed=False, reason=MALFORMED_REASON)
    if not isinstance(payload, dict):
        return Decision(allowed=False, reason=MALFORMED_REASON)
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        return Decision(allowed=False, reason=MALFORMED_REASON)
    return EVALUATORS[client](tool_name, tool_input)


def render_decision(decision: Decision) -> str:
    """Render a denial in the PreToolUse JSON format shared by Claude Code and Codex."""
    if decision.allowed:
        return ""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": decision.reason,
            }
        }
    )
