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
- Organizations: list the organizations of an account and choose the one
  paying its orders by default. (#5)
- Domain orders: register, renew, restore and transfer in a domain. Each order
  is priced with Gandi, checked with a dry run when possible, confirmed by the
  user at its price (in their language) and priced again just before buying.
  Changing the token used for the quote requires a new confirmation.
  The transfer authorization code is typed on the confirmation page, never in
  the conversation. (#5)
- Domain settings: automatic renewal, transfer lock, authorization code,
  contacts and owner (details or change, checked with a dry run where possible),
  nameservers,
  LiveDNS, DNSSEC and its keys, glue records, web redirections, tags, transfer
  out answer and transfer in follow-up, and domain deletion. Destructive
  operations are confirmed by the user. (#5)
- A confirmation can ask the user for a secret (such as an authorization
  code) on its local page, outside the model. (#5)
- MCP App: a "Domains" screen to list the domains of an account (name filter,
  pages), show their details with the full contacts, turn the automatic
  renewal and the transfer lock on or off, change the nameservers, and renew
  or register a domain at an indicative price, confirmed by the server; the
  "Accounts" screen chooses the paying organization. Contacts shown or typed
  in the App never reach the model. (#5)
- Security documentation: the entry points (tools, local pages) and the
  guarantees of the code, each with the tests trying to violate it. (#14)

### Changed

- The declarative endpoint catalogue is shared by the Gandi APIs (`Endpoint`,
  `EndpointToolRunner` with injected result filters, ADR 13); no change of
  tools nor results. (#14)

### Fixed

- Token and confirmation pages: form submissions from browsers were refused
  (`Origin: null` caused by `Referrer-Policy: no-referrer`). (#10)
