<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Privacy policy (draft)

> Draft to be validated by a legal professional; not legal advice. Version
> 0.4, 2026-11-27. **The [French version](privacy-policy.fr.md) is
> authoritative**; this English text and the other languages are
> translations. It will be made accessible from the MCP App UI.
>
> There are no terms of use: use of the software is governed by its license,
> `GPL-2.0-or-later`.

## Who processes your data

`gandi-mcp` is free software that runs on your own computer. Its authors do
not collect, receive or store any of your data. When you use it, you (or your
organization) remain responsible for the data you process with it.

## What the software processes

- **Your Gandi Personal Access Tokens**: stored in your operating system
  keyring, sent only to the Gandi API, never shown to the AI model. You enter
  them in the app or on a temporary page of your own computer, never in the
  conversation.
- **Your account settings** (the name you give each account, its environment,
  whether it is read-only, the default account): stored in a preferences file
  on your computer, without any secret, and sent to the AI model when it lists
  your accounts.
- **The Gandi identity behind a token** (user name and full name): read from
  Gandi when you save a token, displayed to you, never stored.
- **The contact details you give** to register, transfer or change a domain
  (name, address, email, phone): you give them in the conversation, so to the
  AI model, or in the "Domains" screen of the app, from where they do not go
  to the model; the software sends them to Gandi. In Gandi's answers, contact
  details are only shown to the model if you ask for them; the app shows them
  in full to you alone.
- **Transfer authorization codes**: you type them on a temporary page of your
  own computer, never in the conversation; they stay in memory until the
  operation and are only sent to Gandi.
- **Your orders** (domain registration, renewal, restore, transfer): their
  price is shown to you and you confirm them outside the model; they are paid
  by the Gandi organization you choose.
- **Your Gandi data** (domains and their contacts, DNS records, mailboxes,
  certificates, hosting, invoices): fetched from Gandi when a tool needs it,
  kept in memory only, never written to disk by the software.

## Who receives it

- **Gandi**, to perform the operations you request.
- **The provider of your AI assistant** (for example Anthropic or OpenAI):
  tool results are sent to the model you use. Their handling is governed by
  that provider's privacy policy and by your client settings.

## Your rights

The software keeps no copy of your Gandi data. To remove a token and the
settings of its account, remove the account in the software: it deletes both. Exercise your rights on data
held by Gandi or by your AI provider with them directly.

## Contact

Questions about this policy: open an issue on
<https://github.com/bobyone/gandi-mcp/issues>.
