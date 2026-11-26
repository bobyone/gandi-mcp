<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Run the tests and checks

All checks are defined once, in [`.pre-commit-config.yaml`](../../.pre-commit-config.yaml).
The Git hook and the CI run the same commands.

```text
uv sync
uv run pre-commit install          # once per clone: enables the Git hook
uv run pre-commit run --all-files  # every check, as in CI
```

Individual checks:

| Check | Command |
| --- | --- |
| Tests and coverage (threshold 90 %) | `uv run pytest` |
| Lint | `uv run ruff check` |
| Format | `uv run ruff format` |
| Types | `uv run mypy` |
| Translations | `uv run python scripts/check_translations.py` |
| REUSE | `uv run reuse lint` |
| Dependency audit (CI) | `uv run pip-audit --skip-editable` |
| Dependency licenses (CI) | `uv run python scripts/check_licenses.py` |
| DCO sign-offs (CI, pull requests) | `python scripts/check_dco.py origin/main..HEAD` |

Never bypass the hook (`--no-verify`): fix the failing check instead.
