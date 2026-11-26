<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Add a Gandi account

gandi-mcp acts on Gandi with a **Personal Access Token** (PAT) per account.
The token is typed by you on a page of your own computer, never in the
conversation, and kept in your operating system keyring.

## 1. Create a token at Gandi

1. Sign in to the Gandi administration of the environment you want:
   - sandbox (tests, no effect nor cost): <https://admin.sandbox.gandi.net/>;
   - production: <https://admin.gandi.net/>.
2. Open your organization settings, then **Personal Access Tokens**, and
   create a token with the permissions you need (for example domains and
   LiveDNS) and an expiry date.
3. Copy the token; Gandi shows it once.

## 2. Add the account in gandi-mcp

Ask your assistant, for example: "Add my Gandi sandbox account, call it
Tests". The `add_account` tool then shows you a page:

- in the client, when it supports URL elicitation (you are asked to open a
  link);
- otherwise in your browser, opened by gandi-mcp itself.

Paste the token in the **Personal Access Token** field and select **Save**.
gandi-mcp asks Gandi who the token belongs to; the page shows the Gandi user
name when the account is saved. The first account becomes the default one.

The page is only served on `127.0.0.1`, works once and expires after 10
minutes (`token_entry.timeout_seconds`).

## 3. Manage the account

| Request | Tool |
| --- | --- |
| List the accounts | `list_accounts` |
| Rename, make default, make read-only | `update_account` (turning read-only off asks for your confirmation) |
| Replace an expired token | `replace_account_token` |
| Move between sandbox and production | `change_account_environment` (needs a token of the new environment) |
| Remove the account and its token | `remove_account` (asks for your confirmation) |

## When something fails

- "Gandi refused this token for this environment": the token is mistyped,
  expired, or belongs to the other environment.
- "The keyring of the system is unavailable": see the
  `gandi-mcp-troubleshoot` skill.
- No page opened: your client has no URL elicitation and no browser could be
  opened (for example over SSH); run gandi-mcp on a computer with a browser.
