<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 1. Project framing

- Status: accepted
- Date: 2026-11-26
- Issue: #1

## Context

Gandi exposes its services (domains, LiveDNS, email, certificates, hosting,
cloud, billing, organizations, templates) through its public API v5. Users
want to manage them from their AI assistant (Claude Desktop, Claude Code,
Codex) on their own computer.

## Decision

- **Nature**: an MCP application in **personal mode only**: a local MCP server
  over `stdio`. No web mode is provided. It ships an **MCP App** (a UI rendered
  by the client); every operation stays available as a pure MCP tool, the UI
  only adds comfort (visualization, input, editing).
- **Users**: individuals and small businesses with some technical knowledge, on
  Windows, macOS and Linux. The UI targets WCAG 2.1 level AA.
- **Authentication**: Gandi **Personal Access Tokens** (PAT). Several named
  accounts can be configured, one being the default. The PAT is entered **in
  the MCP App UI**, through a tool visible to the app only, so it never enters
  the model context. Clients without MCP App support use a temporary page on
  `localhost` protected by a single-use token, opened through URL-mode
  elicitation. PATs are stored in the operating system keyring.
- **Data**: nothing is stored locally except PATs (keyring) and preferences.
  Gandi data is fetched on demand. The LLM provider receives tool results and
  is declared as a recipient in the records of processing.
- **Safety**: destructive or billable operations (purchase, renewal, transfer,
  deletion) require a confirmation requested by the server (elicitation, else
  MCP App UI, else localhost link). The Gandi sandbox API can be targeted.
- **Openness**: public repository, `GPL-2.0-or-later`, contributions certified
  by the Developer Certificate of Origin (DCO).
- **Operations**: no server, hence no container nor deployment target; pull
  requests are tested locally (`gh pr checkout`, then the quick-start).
- **Scope**: the whole Gandi API v5, delivered in batches, each with its own
  issue and validated design:
  1. core (Gandi client, accounts, PAT, sandbox, confirmation), Domain, LiveDNS;
  2. Email, Certificate;
  3. Billing, Organization, Template;
  4. Simple Hosting, Cloud/VPS, LinkHosting.

## Alternatives considered

- **Pure MCP without UI**: lighter, but entering a PAT and editing DNS zones
  are much more comfortable in a UI. Rejected.
- **Gandi OAuth**: requires registering an application with Gandi and a
  redirect flow; PATs are simpler for a personal tool. Deferred.
- **Local cache of Gandi data**: fewer API calls, but personal data to protect
  and expire. Rejected for now.
- **GPL-2.0-only**: incompatible with Apache-2.0 dependencies. Rejected.

## Consequences

- No web-mode rule applies (multi-user rights, mandatory content guard).
- The UI must be internationalized in every target language.
- A fallback path is required for clients that cannot render MCP Apps.
