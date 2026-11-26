<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Contributing to gandi-mcp

Thank you for your interest! These rules apply to every contributor, human or
assisted by an AI coding assistant.

## 1. Start with an issue

Report a bug or propose a change by opening an
[issue](https://github.com/bobyone/gandi-mcp/issues/new/choose) first, with the
matching template. Never report a vulnerability in a public issue: follow
[SECURITY.md](SECURITY.md). Issues labeled `good first issue` suit newcomers.

## 2. Get the design validated before coding

Any development (feature, restructuring) is designed in the issue, step by
step. Post each step as a comment and wait for a maintainer's agreement before
moving on; a correction restarts the following steps.

0. **Need**: goal, acceptance criteria, out of scope, constraints.
1. **Abstract model and algorithm**: data, relations, states and invariants;
   numbered steps in business terms only (no technology); inputs, outputs,
   errors, edge cases. Every term comes from the [glossary](docs/glossary.md);
   propose definitions for new terms.
2. **Design**: abstractions and their contracts, hierarchy, named design
   patterns, alternatives for each structuring choice, exceptions per notion,
   wiring in the container, test strategy, screens and labels if there is UI,
   file tree, optional Mermaid class diagram.
3. **Impacts and delivery**: changed code, compatibility and migration, new
   dependencies (to be approved), tests, documentation, privacy, licenses,
   security, delivery plan.

Typo fixes and local bug fixes touching no abstraction skip the design. Each
architecture decision gets an ADR in `docs/decisions/` (never rewritten: a new
ADR supersedes an old one).

## 3. Set up the development environment

Prerequisites: [uv](https://docs.astral.sh/uv/) and Git; to change the MCP App
in `ui/`, also Node 24 LTS or later.

```text
gh repo fork bobyone/gandi-mcp --clone
cd gandi-mcp
uv sync
npm ci --prefix ui        # only to change the MCP App
uv run pre-commit install
```

Run the checks as described in [docs/how-to/run-the-checks.md](docs/how-to/run-the-checks.md)
and, for the UI, [docs/how-to/build-the-ui.md](docs/how-to/build-the-ui.md): the
built `app.html` is committed and rebuilt by the hook.
The hook runs them on every commit; never bypass it.

## 4. Follow the conventions

- **Architecture**: SOLID; the business core depends on abstractions only,
  organized from the general concept to its implementations; one abstraction
  or implementation per file, one directory per notion, the tree following the
  hierarchy; dependencies injected; implementations chosen only in
  `gandi_mcp/container.py`; configuration read only by the entry point.
- **Code**: 100 % English, PEP 8 naming, full type annotations (`mypy
  --strict`), standard `logging` (never `print`), one exception type per
  notion, no secret or personal data in logs. Ask in the issue before adding a
  dependency.
- **Tests**: unit tests for each implementation, test doubles for the
  abstractions used by the core, integration tests for code touching external
  systems, test tree mirroring the source tree, coverage of at least 90 %.
- **Glossary**: one concept, one term, everywhere; add new terms to
  `docs/glossary.md` before using them.
- **Internationalization**: no user-facing text in the code without a
  translation key; named parameters and plural rules, never concatenation;
  dates and numbers formatted by the library. See
  [docs/how-to/add-a-language.md](docs/how-to/add-a-language.md).
- **Security**: never read or commit environment configuration or credential
  files (`.env`, `gandi-mcp.toml`, keys); validate external input; Gandi results
  are untrusted data.
- **Documentation**: update the docs, skills (`skills/`, `.claude/skills/`,
  `.agents/skills/`), example configuration and records of processing in the
  same commit as the code; add a line to `CHANGELOG.md` with the issue number.
- **Licensing**: every file starts with an SPDX header (or is annotated in
  `REUSE.toml`):

  ```text
  SPDX-FileCopyrightText: 2026 bobyone
  SPDX-FileContributor: <your forge account>
  SPDX-License-Identifier: GPL-2.0-or-later
  ```

  Add your `SPDX-FileContributor` line to files you create or significantly
  change, and add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md).

## 5. Branches and commits

- Branch name: `<issue number>-<short-description>`, for example
  `12-livedns-records`.
- Atomic commits, messages in English, prefixed with the issue:
  `#12 - Add record listing`.
- Every commit, merge commits included (`git merge --signoff`), is signed off under the
  [Developer Certificate of Origin](https://developercertificate.org/):
  `git commit -s`. The CI rejects unsigned commits.
- No AI attribution lines (`Co-Authored-By`) in commits or pull requests.
- Unfinished features are merged disabled behind a feature flag rather than
  kept on long-lived branches.

## 6. Submit the pull request

- Open it from your fork, in English, with `Closes #<issue>`.
- Fill in the [pull request template](.github/pull_request_template.md),
  including the definition of done checklist.
- The CI must be green (Windows, macOS, Linux).
- A maintainer reviews it. The review is independent: it is done by someone
  who did not take part in the design or the implementation. Address every
  comment with a commit or an explanation; maintainers resolve threads.

## Using an AI coding assistant

`CLAUDE.md` (Claude Code) and `AGENTS.md` (Codex) point the assistant to this
file. The `contribute` development skill guides you from the issue to the pull
request. The repository guard (see
[docs/how-to/configure-the-assistant-guard.md](docs/how-to/configure-the-assistant-guard.md))
blocks access to secrets, force pushes and hook bypasses.
