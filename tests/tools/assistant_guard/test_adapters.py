# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the client adapters and the hook entry point."""

import json

import pytest
from tools.assistant_guard.adapters import evaluate_hook_input, render_decision
from tools.assistant_guard.policy import MALFORMED_REASON

from tools.assistant_guard import hook


def payload(tool_name: str, **tool_input: object) -> str:
    return json.dumps({"tool_name": tool_name, "tool_input": tool_input})


@pytest.mark.parametrize(
    ("client", "raw", "allowed"),
    [
        ("claude", payload("Read", file_path="/repo/.env"), False),
        ("claude", payload("Read", file_path="/repo/.env.example"), True),
        ("claude", payload("Edit", file_path="config.toml"), False),
        ("claude", payload("NotebookEdit", notebook_path="a.ipynb"), True),
        ("claude", payload("Grep", pattern="TOKEN", glob=".env*"), True),
        ("claude", payload("Grep", pattern="TOKEN", path=".env"), False),
        ("claude", payload("Bash", command="git push --force"), False),
        ("claude", payload("PowerShell", command="Get-Content .env"), False),
        ("claude", payload("WebFetch", url="https://example.org"), True),
        ("codex", payload("Bash", command=["bash", "-lc", "cat .env"]), False),
        ("codex", payload("Bash", command="git status"), True),
        ("codex", payload("apply_patch", command="*** Update File: .env\n+X=1\n"), False),
        ("codex", payload("apply_patch", command="*** Add File: docs/a.md\n+x\n"), True),
        ("codex", payload("apply_patch", command=None), False),
        ("codex", payload("mcp__fs__read", path=".env"), True),
    ],
)
def test_evaluate_hook_input(client: str, raw: str, allowed: bool) -> None:
    assert evaluate_hook_input(client, raw).allowed is allowed


@pytest.mark.parametrize(
    "raw", ["not json", "[]", json.dumps({"tool_name": 1}), json.dumps({"tool_input": []})]
)
def test_malformed_input_is_denied_without_echo(raw: str) -> None:
    decision = evaluate_hook_input("claude", raw)

    assert decision.reason == MALFORMED_REASON


def test_render_denial_and_silence_on_allow() -> None:
    denial = json.loads(hook.run(["claude"], payload("Read", file_path=".env")))

    assert denial["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert hook.run(["codex"], payload("Bash", command="ls")) == ""
    assert render_decision(evaluate_hook_input("claude", payload("Bash", command="ls"))) == ""


def test_hook_rejects_unknown_client() -> None:
    with pytest.raises(SystemExit):
        hook.run(["vim"], "{}")
