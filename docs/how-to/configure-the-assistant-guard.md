<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Configure the assistant guard

Coding assistants working on this repository must not read local environment
or credential files, force-push, or bypass Git hooks. The repository enforces
this with:

| Control | Claude Code | Codex |
| --- | --- | --- |
| Tool hook | [`.claude/settings.json`](../../.claude/settings.json) `PreToolUse` | [`.codex/hooks.json`](../../.codex/hooks.json) `PreToolUse` |
| File access | `permissions.deny` in `.claude/settings.json` | permission profile in [`.codex/config.toml`](../../.codex/config.toml) |
| Commands | `permissions.deny` / `ask` | [`.codex/rules/git.rules`](../../.codex/rules/git.rules) |

Both hooks call the same policy, [`tools/assistant_guard/policy.py`](../../tools/assistant_guard/policy.py),
through one adapter per client. Example files (`gandi-mcp.example.toml`,
`*.example`) stay readable.

## Enable

- **Claude Code**: nothing to do; project settings load automatically. `uv`
  must be on the `PATH`.
- **Codex**: trust the project, then review and trust the project hook. Check
  that the `gandi-mcp` permission profile is active (legacy `sandbox_mode`
  settings take precedence over it).

## Check

```text
uv run pytest tests/tools
echo '{"tool_name":"Read","tool_input":{"file_path":".env"}}' | uv run --no-project python tools/assistant_guard/hook.py claude
```

The second command prints a `deny` decision. With Codex, also run
`codex execpolicy check --pretty --rules .codex/rules/git.rules -- git push --force`.

`tests/tools/assistant_guard/test_codex_profile.py` enforces the committed
permission profile with `codex sandbox` on synthetic files: protected files
must be unreadable, their examples readable. It runs when the Codex CLI is on
the `PATH` (or `CODEX_CLI` gives its path) and its sandbox is available; on
Windows this requires the elevated sandbox backend, otherwise the test is
skipped. The CI job `Codex permission profile` runs it on Linux with
`CODEX_PROFILE_REQUIRED=1`, so it can never be skipped there.

## Change the rules

Edit `PROTECTED_FILE_PATTERNS`, `ALLOWED_EXAMPLE_PATTERNS` or the Git checks
in `policy.py`, add tests in `tests/tools/assistant_guard/`, and keep the
static deny lists of both clients consistent.
