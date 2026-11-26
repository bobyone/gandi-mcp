<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Glossary

One concept, one term, used everywhere (UI, messages, documentation, code,
API). Add a term here before using it. UI labels are given per language once
the term appears in the UI; until then the column says "not displayed".

| Term | Definition | Code identifier | UI label |
| --- | --- | --- | --- |
| Gandi | The registrar and hosting provider whose public API v5 this project uses. | `gandi` | Gandi (never translated) |
| Gandi API | The Gandi public HTTP API, version 5. | `gandi_api` | not displayed |
| Sandbox | The Gandi test environment, where operations have no real effect nor cost; it has its own accounts and tokens. | `sandbox` | not displayed yet |
| Personal mode | The local MCP server running on the user's computer over `stdio`. | `personal_mode` | not displayed |
| MCP App | The UI provided by the server and rendered by the MCP client. | `mcp_app` | not displayed |
| Tool | An operation exposed by the server to the MCP client. | `tool` | not displayed |
| Account | A Gandi identity configured in the personal mode: a name chosen by the user and a Personal Access Token. | `account` | not displayed yet |
| Default account | The account used when a tool call names no account. | `default_account` | not displayed yet |
| Personal Access Token (PAT) | A Gandi secret granting API rights to an account; stored in the OS keyring only. | `personal_access_token` | not displayed yet |
| Confirmation | The user's explicit agreement, requested by the server, before a destructive or billable operation. | `confirmation` | not displayed yet |
| Destructive operation | An operation that deletes or irreversibly changes a Gandi resource. | `destructive` | not displayed |
| Billable operation | An operation that charges the Gandi account (purchase, renewal, transfer). | `billable` | not displayed |
| Environment | The Gandi target of an account: production or sandbox. | `environment` | not displayed yet |
| Production | The real Gandi environment, where operations have effects and costs. | `production` | not displayed yet |
| Read-only account | An account whose write operations are all refused. | `read_only` | not displayed yet |
| Secret store | The operating system keyring, the only place where a Personal Access Token is kept. | `secret_store` | not displayed |
| Preferences | Local settings without any secret: the accounts and the default account. | `preferences` | not displayed |
| Token entry session | A temporary local page, protected by a single-use code, to enter a Personal Access Token without the MCP App. | `token_entry_session` | not displayed yet |
| Operation | A call to Gandi on behalf of an account. | `operation` | not displayed |
| Read operation | An operation that only reads Gandi resources. | `read_operation` | not displayed |
| Write operation | An operation that changes Gandi resources; destructive and billable operations are write operations. | `write_operation` | not displayed |
| Confirmation channel | A way to ask for a confirmation: elicitation, MCP App or local link. | `confirmation_channel` | not displayed |
| Untrusted data | Content coming from tool results or free inputs, which may contain prompt injection. | `untrusted` | not displayed |
