# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Client-independent policy protecting secrets and Git safeguards from coding assistants.

The policy denies:
- access to local environment configuration and credential files (their examples stay allowed);
- force pushes;
- bypasses of the mandatory Git hooks.
"""

import re
import shlex
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import PurePosixPath, PureWindowsPath

PROTECTED_FILE_PATTERNS: tuple[str, ...] = (
    ".env",
    ".env.*",
    "*.env",
    "gandi-mcp.toml",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "credentials*.json",
    ".netrc",
    "_netrc",
    ".git-credentials",
    ".pypirc",
    ".npmrc",
    "id_rsa*",
    "id_ed25519*",
    "id_ecdsa*",
)
ALLOWED_EXAMPLE_PATTERNS: tuple[str, ...] = (
    "*.example",
    "*.example.*",
    "*.sample",
    "*.template",
    "*.pub",
)
PROTECTED_DIRECTORIES: tuple[str, ...] = (".ssh", ".aws", ".gnupg", ".azure", ".kube")

SHELL_OPERATORS = frozenset({";", "&&", "||", "|", "&", "\n", "(", ")", "|&"})
FORCE_PUSH_OPTIONS = frozenset({"--force", "-f", "--force-with-lease", "--force-if-includes"})
HOOK_BYPASS_SUBCOMMANDS = frozenset({"commit", "push", "merge", "am", "rebase", "cherry-pick"})
HOOK_BYPASS_ENVIRONMENT = re.compile(r"(^|[\s;&|$:])(SKIP|PRE_COMMIT_ALLOW_NO_CONFIG)\s*=", re.I)
HEREDOC_START = re.compile(r"(?<!<)<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
HERE_STRING_START = re.compile(r"@(['\"])\s*$")
GIT_OPTIONS_WITH_VALUE = frozenset({"-c", "-C", "--git-dir", "--work-tree", "--namespace"})

MALFORMED_REASON = "Request blocked: the assistant guard could not parse it."


@dataclass(frozen=True)
class Decision:
    """Outcome of a policy check."""

    allowed: bool
    reason: str = ""


ALLOW = Decision(allowed=True)


def _name_parts(path: str) -> list[str]:
    """Split a path written with either separator into its parts."""
    if "\\" in path:
        return list(PureWindowsPath(path).parts)
    return list(PurePosixPath(path).parts)


def is_protected_path(path: str) -> bool:
    """Tell whether a path designates a protected file, case-insensitively."""
    parts = [part.lower() for part in _name_parts(path.strip().strip("\"'"))]
    if not parts:
        return False
    if any(part in PROTECTED_DIRECTORIES for part in parts[:-1]):
        return True
    name = parts[-1]
    if any(fnmatchcase(name, pattern) for pattern in ALLOWED_EXAMPLE_PATTERNS):
        return False
    return any(fnmatchcase(name, pattern) for pattern in PROTECTED_FILE_PATTERNS)


def check_path(path: object) -> Decision:
    """Check a file path given to a file tool."""
    if not isinstance(path, str):
        return Decision(allowed=False, reason=MALFORMED_REASON)
    if is_protected_path(path):
        return Decision(
            allowed=False,
            reason="Reading or writing local environment or credential files is forbidden; "
            "use the matching example file instead.",
        )
    return ALLOW


def strip_inline_documents(command: str) -> str:
    """Remove the bodies of shell heredocs and PowerShell here-strings.

    Their content is data passed to a command, not shell syntax: quotes inside it
    must not make the command unparseable. The command lines themselves are kept.
    """
    kept: list[str] = []
    closing: list[str] = []
    for line in command.splitlines():
        if closing:
            if line.strip() == closing[0] or (
                closing[0] in {"'@", '"@'} and line.startswith(closing[0])
            ):
                closing.pop(0)
            continue
        kept.append(line)
        closing.extend(match[1] for match in HEREDOC_START.findall(line))
        here_string = HERE_STRING_START.search(line)
        if here_string:
            kept[-1] = line[: here_string.start()] + "HERE-STRING"
            closing.append(here_string[1] + "@")
    return "\n".join(kept)


def _split_segments(command: str) -> list[list[str]]:
    """Tokenize a shell command and split it into simple commands."""
    lexer = shlex.shlex(strip_inline_documents(command), posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""  # keep Windows path separators literal
    segments: list[list[str]] = [[]]
    for token in lexer:
        if token in SHELL_OPERATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def _git_arguments(segment: list[str]) -> tuple[list[str], list[str]] | None:
    """Return the Git global options and the arguments after them, if the segment runs Git."""
    for index, token in enumerate(segment):
        executable = _name_parts(token)[-1].lower() if token else ""
        if executable in {"git", "git.exe"}:
            rest = segment[index + 1 :]
            options: list[str] = []
            position = 0
            while position < len(rest) and rest[position].startswith("-"):
                options.append(rest[position])
                if rest[position] in GIT_OPTIONS_WITH_VALUE and position + 1 < len(rest):
                    options.append(rest[position + 1])
                    position += 1
                position += 1
            return options, rest[position:]
    return None


def _is_force_push(arguments: list[str]) -> bool:
    if not arguments or arguments[0] != "push":
        return False
    for argument in arguments[1:]:
        if argument.split("=", 1)[0] in FORCE_PUSH_OPTIONS:
            return True
        if argument.startswith("+") and len(argument) > 1:
            return True
        if re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", argument):
            return True
    return False


def _is_hook_bypass(options: list[str], arguments: list[str]) -> bool:
    if any("core.hookspath" in option.lower() for option in options):
        return True
    if not arguments or arguments[0] not in HOOK_BYPASS_SUBCOMMANDS:
        return False
    for argument in arguments[1:]:
        if argument == "--no-verify":
            return True
        if arguments[0] == "commit" and re.fullmatch(r"-[a-zA-Z]*n[a-zA-Z]*", argument):
            return True
    return False


def _check_segment(segment: list[str]) -> Decision:
    """Check one simple command."""
    for token in segment:
        candidate = token.split("=", 1)[-1] if token.startswith("-") else token
        if is_protected_path(candidate):
            return check_path(candidate)
    git = _git_arguments(segment)
    if git is None:
        if segment[:2] == ["pre-commit", "uninstall"]:
            return Decision(allowed=False, reason="Uninstalling the Git hooks is forbidden.")
        return ALLOW
    options, arguments = git
    if _is_force_push(arguments):
        return Decision(
            allowed=False, reason="Force push is forbidden without the maintainer's consent."
        )
    if _is_hook_bypass(options, arguments):
        return Decision(allowed=False, reason="Bypassing the Git hooks is forbidden.")
    return ALLOW


def check_command(command: object) -> Decision:
    """Check a shell command; a compound command is denied if any part violates the policy."""
    if not isinstance(command, str):
        return Decision(allowed=False, reason=MALFORMED_REASON)
    if HOOK_BYPASS_ENVIRONMENT.search(command):
        return Decision(allowed=False, reason="Skipping pre-commit hooks is forbidden.")
    try:
        segments = _split_segments(command)
    except ValueError:
        return Decision(allowed=False, reason=MALFORMED_REASON)
    return next(
        (decision for segment in segments if not (decision := _check_segment(segment)).allowed),
        ALLOW,
    )
