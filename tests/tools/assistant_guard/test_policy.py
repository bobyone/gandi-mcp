# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Unit tests of the assistant guard policy."""

import pytest
from tools.assistant_guard.policy import MALFORMED_REASON, check_command, check_path


@pytest.mark.parametrize(
    "path",
    [
        ".env",
        "sub/dir/.env",
        r"C:\repo\.ENV",
        ".env.local",
        "prod.env",
        "config.toml",
        "nested/Config.TOML",
        "server.pem",
        "credentials.json",
        "~/.ssh/config",
        r"C:\Users\me\.aws\config",
        ".git-credentials",
        "id_ed25519",
    ],
)
def test_protected_paths_are_denied(path: str) -> None:
    decision = check_path(path)

    assert not decision.allowed
    assert path not in decision.reason


@pytest.mark.parametrize(
    "path",
    [".env.example", "config.example.toml", "sub/.ENV.EXAMPLE", "id_ed25519.pub", "README.md", ""],
)
def test_examples_and_ordinary_files_are_allowed(path: str) -> None:
    assert check_path(path).allowed


def test_non_string_path_is_malformed() -> None:
    assert check_path(None).reason == MALFORMED_REASON


@pytest.mark.parametrize(
    "command",
    [
        "cat .env",
        r"Get-Content -Path .\.env",
        "type config.toml",
        r"type C:\x\config.toml",
        r"Get-Content 'C:\Program Files\app\.env'",
        "grep TOKEN --file=.env",
        "git push --force",
        "git push -f origin main",
        "git push origin +main",
        "git push --force-with-lease origin 1-x",
        "git -C repo push -uf origin main",
        "git commit --no-verify -m x",
        "git commit -nm x",
        "git push --no-verify",
        "git -c core.hooksPath=/dev/null commit -m x",
        "SKIP=pytest git commit -m x",
        "$env:SKIP='mypy'; git commit -m x",
        "pre-commit uninstall",
        "git status && git push --force",
        "echo ok | git push -f",
        "/usr/bin/git push --force",
    ],
)
def test_dangerous_commands_are_denied(command: str) -> None:
    assert not check_command(command).allowed


@pytest.mark.parametrize(
    "command",
    [
        "cat .env.example",
        "git push -u origin 1-project-initialization",
        "git commit -s -m '#1 - Add guard'",
        "git status; git log --oneline",
        "uv run pytest -q",
        "echo 'no-verify is a word'",
    ],
)
def test_ordinary_commands_are_allowed(command: str) -> None:
    assert check_command(command).allowed


@pytest.mark.parametrize("command", ["echo 'unterminated", 42])
def test_malformed_commands_are_denied(command: object) -> None:
    assert check_command(command).reason == MALFORMED_REASON


HEREDOC = "cat > notes.md <<'EOF'\nThe user's token: don't share\nEOF\ngit status\n"
HEREDOC_THEN_FORCE = "cat > a.txt <<EOF\nit's\nEOF\ngit push --force\n"
HERE_STRING = "git commit -s -m @'\nThe user's change\n'@\n"


@pytest.mark.parametrize("command", [HEREDOC, HERE_STRING])
def test_inline_document_bodies_are_data(command: str) -> None:
    assert check_command(command).allowed


def test_commands_after_a_heredoc_are_still_checked() -> None:
    assert not check_command(HEREDOC_THEN_FORCE).allowed


def test_heredoc_redirection_to_protected_file_is_denied() -> None:
    assert not check_command("cat > .env <<'EOF'\nTOKEN=x\nEOF\n").allowed
