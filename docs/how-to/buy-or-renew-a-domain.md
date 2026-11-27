<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Buy or renew a domain

Registering, renewing, restoring and transferring a domain to Gandi are
orders: they charge the prepaid account of the paying organization. Nothing
is bought until you accept the price in the confirmation shown by the server
(ADR 7). Practice with a [sandbox](use-the-sandbox.md) account, where orders
cost nothing.

## Choose the paying organization

An order is paid by the paying organization of the account; without one,
Gandi chooses. Choose it once:

- in the conversation: "list my organizations", then "make ... the paying
  organization";
- in the MCP App: **Accounts** tab, **Actions** of the account, **Choose the
  paying organization**.

## From the conversation

Ask, for example, "register example.fr for 2 years" or "renew example.com".
The assistant checks the availability or the renewal information, asks you
for the owner of a new domain, then places the order (see the
`gandi-mcp-buy-domain` skill). The server shows you the exact price, in your
language, outside the conversation; once you accepted, tell the assistant.
For a transfer, you type the authorization code on the confirmation page,
never in the conversation.

## From the MCP App

1. **Register**: in the **Domains** tab, select **Register a domain**, type
   the name and select **Check availability**. If it is available, choose the
   **Duration** and fill in the **Owner**: they are also the admin, tech and
   billing contact. The price shown is indicative.
2. **Renew**: open the **Details** of a domain and select **Renew**, then
   choose the **Duration**.
3. Select **Register a domain** or **Renew**: the server shows the exact
   amount in its confirmation. Accept or refuse it there, then select
   **Continue** in the App.

## If the order does not go through

- The price changed between the confirmation and the order: nothing is
  bought; order again to see the new price.
- Several prices apply (launch period of an extension): nothing is bought;
  try later or order in the Gandi administration.
- A registration takes a few minutes at Gandi: ask the assistant to follow
  it, or open the domain again later.
