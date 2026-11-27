<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage your domains

Look up and change the domains of a Gandi account, from the conversation or
from the "Domains" screen of the MCP App. Try it first with a
[sandbox](use-the-sandbox.md) account.

## From the conversation

Ask your assistant, for example "list my domains", "show the nameservers of
example.com" or "turn off the automatic renewal of example.com". It uses the
`domain_*` tools (see the `gandi-mcp-manage-domains` skill):

- reading never changes anything; contact details (names, addresses, emails)
  and the authorization code are only sent to the model when you ask for
  them;
- destructive changes (nameservers, owner, DNSSEC keys, deletion, transfer
  unlock...) are confirmed by you, outside the conversation: in a dialog of
  your client or on a page opened in your browser. Then tell the assistant
  you answered;
- a read-only account refuses every change.

## From the MCP App

Ask "open the Gandi app", then select the **Domains** tab:

1. Choose the **Account**, and filter by name if needed (`*` is a wildcard,
   for example `*.fr`). The table shows the expiry date, the automatic
   renewal, the transfer lock and the Gandi statuses, page by page.
2. Select **Details** on a domain: its dates, statuses, nameservers, tags and
   full domain contacts. What the App shows is never sent to the model.
3. From the details, turn the automatic renewal or the transfer lock on or
   off, **Change the nameservers** (one per line) or **Renew** (see
   [buy or renew a domain](buy-or-renew-a-domain.md)).
4. When the server asks for a confirmation, answer it in the window it
   opens, then select **Continue** in the App.

Glue records, DNSSEC, web redirections, transfers and owner changes are only
available from the conversation for now.

## When something fails

The message says what happened and how to fix it. See the
`gandi-mcp-troubleshoot` skill for common errors.
