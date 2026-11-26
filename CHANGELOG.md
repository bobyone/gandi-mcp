<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

### Added

- Project initialization: framing and technology stack ADRs, MCP server
  skeleton over `stdio`, configuration example, translation catalogs for 42
  languages, CI on Windows, macOS and Linux, assistant guard for Claude Code
  and Codex, plugin and skills skeleton, REUSE compliance, records of
  processing. (#1)
- Configuration keys for the preferences file, the Gandi base URLs and
  timeout, the confirmation and token entry validity, and the free input
  limit; unknown keys are rejected. (#4)
- Gandi accounts: tools to list, add, rename, make default, make read-only,
  re-authenticate, move between production and sandbox, and remove accounts.
  Personal Access Tokens are typed on a local page (never in the
  conversation), checked with Gandi and kept in the OS keyring; preferences
  are kept in a local JSON file. Destructive and billable operations are
  confirmed by the user through elicitation or a local page. (#4)
- MCP App: an "Accounts" screen (React-Bootstrap, themed by the host, in 43
  languages) to add, rename, re-authenticate, move, lock and remove accounts;
  tokens typed there go to app-only tools, never to the model. (#4)
- Domains (read): tools to check availability and prices, list the
  extensions, list and describe domains, and read their contacts,
  nameservers, LiveDNS and DNSSEC status, DNSSEC keys, glue records, web
  redirections, tags, renewal and restore information, trademark claims and
  the follow-up of registrations, owner changes and transfers in. Contact
  details, email addresses, owner names and authorization codes are only sent
  to the model on request; Gandi texts longer than `content.max_free_input`
  are withheld from it. (#5)
