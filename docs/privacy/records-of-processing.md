<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Records of processing

> Template describing the processing performed by the software, for the
> person or organization that installs it (the controller), as required by
> Article 30 GDPR. Complete the bracketed fields. A purely personal use by an
> individual may fall under the household exemption (Article 2(2)(c) GDPR).
> Draft to be validated by a legal professional; not legal advice.

The software runs on the user's computer. Its authors receive no data.

## P1. Management of Gandi resources from an AI assistant

| Field | Description |
| --- | --- |
| Controller | [Name and contact of the person or organization using the software] |
| Purpose | Let the user read and manage their Gandi resources (domains, DNS, email, certificates, hosting, billing, organizations) through an MCP client. |
| Legal basis | [Performance of a contract with Gandi / legitimate interest of the controller in managing its own resources] |
| Data subjects | The user; domain contacts (owner, administrative, technical, billing); mailbox and forwarding users; organization members. |
| Data categories | Identification and contact data of domain contacts (name, postal address, email, phone, organization); email addresses of mailboxes and forwards; billing data (invoices, amounts, payment status); technical data (domain names, DNS records, IP addresses of servers). |
| Recipients | Gandi SAS (France), service provider of the controller; the provider of the LLM used by the MCP client (for example Anthropic or OpenAI), which receives tool results. |
| Transfers outside the EU | Depending on the LLM provider: [for example United States, under the provider's data processing terms and transfer mechanism]. Gandi processes data in the EU. |
| Retention | The software stores no Gandi data: it fetches it on demand and keeps it in memory for the duration of a tool call. Retention by the LLM provider follows its own policy and the client's settings: [to complete]. |
| Security measures | HTTPS to the Gandi API; logs contain no personal data nor secret; tool results are marked as untrusted data; destructive and billable operations require the user's confirmation, given outside the model (MCP App dialog, elicitation or local page); read-only accounts refuse every write operation. |

## P2. Management of the accounts and their Personal Access Tokens

| Field | Description |
| --- | --- |
| Controller | [Same as P1] |
| Purpose | Configure the Gandi accounts used by the software and authenticate to the Gandi API on their behalf. |
| Legal basis | [Same as P1] |
| Data subjects | The user. |
| Data categories | Account settings: name chosen by the user, environment (production or sandbox), read-only flag, default account. Gandi Personal Access Token (secret). Gandi identity behind the token (user name and full name), read when the token is saved, displayed to the user and never stored. |
| Recipients | Gandi SAS, to which the token is sent to authenticate each request and which returns the identity. The provider of the LLM receives the account settings in tool results, never the token nor the identity. |
| Transfers outside the EU | Account settings: depending on the LLM provider, as in P1. Token and identity: none. |
| Retention | Account settings and token: until the user removes the account in the software (the token may expire earlier at Gandi). Token entry sessions and pending confirmations: in memory only, at most `token_entry.timeout_seconds` (default 10 minutes) and `confirmation.timeout_seconds` (default 5 minutes). |
| Security measures | The token is kept in the operating system keyring only, never in a file nor in logs, and never passes through the model: it is entered in the MCP App UI through an app-only tool, or on a local page served on `127.0.0.1` only, protected by a single-use code and shown through URL elicitation or the browser, never through the model. Account settings are kept in a local preferences file without any secret, written atomically. |
