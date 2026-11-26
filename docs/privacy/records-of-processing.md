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
| Security measures | HTTPS to the Gandi API; logs contain no personal data nor secret; tool results are marked as untrusted data; destructive and billable operations require confirmation. |

## P2. Storage of Personal Access Tokens

| Field | Description |
| --- | --- |
| Controller | [Same as P1] |
| Purpose | Authenticate to the Gandi API on behalf of each configured account. |
| Legal basis | [Same as P1] |
| Data subjects | The user. |
| Data categories | Account name chosen by the user; Gandi Personal Access Token (secret). |
| Recipients | None. The token is sent only to the Gandi API; it never reaches the model. |
| Transfers outside the EU | None. |
| Retention | Until the user removes the account in the software, or the token expires at Gandi. |
| Security measures | Stored in the operating system keyring only, never in a file nor in logs; entered in the MCP App UI through an app-only tool, or through a temporary localhost page protected by a single-use token. |
