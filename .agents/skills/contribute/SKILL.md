---
name: contribute
description: Guide a contributor to gandi-mcp step by step, from the issue to the merged pull request (design validation, branch, checks, DCO-signed commits, pull request with the definition of done). Use when someone wants to fix a bug, add a feature or otherwise change this repository.
---

# Contribute to gandi-mcp

`CONTRIBUTING.md` is the reference: read it first and follow it. This skill
only drives its steps with the project commands.

1. **Issue**: find or open the issue (`gh issue list`, `gh issue create` with
   the bug or feature template). Security issues go through `SECURITY.md`.
2. **Design**: unless it is a typo or a local fix, post the design steps 0 to 3
   of `CONTRIBUTING.md` in the issue, one at a time, and wait for the
   maintainer's agreement after each. Use terms from `docs/glossary.md`.
3. **Environment**: `uv sync`, then `uv run pre-commit install`.
4. **Branch**: `git switch -c <issue>-<short-description>`.
5. **Implement** the validated design. If it must change, stop and propose the
   change in the issue. Update docs, glossary, translations, skills,
   `CHANGELOG.md`, `config.example.toml`, records of processing and SPDX
   headers in the same commits.
6. **Check**: `uv run pre-commit run --all-files`. Fix failures; never bypass
   the hook.
7. **Commit**: `git commit -s -m "#<issue> - <message>"`, atomic commits, no AI
   attribution lines.
8. **Pull request**: push the branch to your fork, then `gh pr create` with
   `Closes #<issue>` and the completed template. Wait for a green CI and an
   independent review. Answer each comment with a commit or an explanation,
   and let the maintainer resolve threads.
