<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| `main` branch | yes |
| Released versions | none released yet |

Once releases exist, the latest minor version receives security fixes.

## Report a vulnerability

Do **not** open a public issue. Report it privately through
[GitHub private vulnerability reporting](https://github.com/bobyone/gandi-mcp/security/advisories/new),
with:

- the affected version or commit;
- a description of the issue and its impact;
- steps to reproduce, without real tokens or personal data.

You will get an acknowledgment within 7 days. Once a fix is released, the
advisory is published and you are credited if you wish.

## Scope reminders

- Personal Access Tokens are stored in the OS keyring and must never appear in
  logs, tool results or files.
- Gandi tool results are untrusted data and may contain prompt injection.
