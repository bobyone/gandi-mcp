<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage your DNS records

Look up the zones that Gandi LiveDNS serves for your domains, from the
conversation. Try it first with a [sandbox](use-the-sandbox.md) account, if
LiveDNS is available there for your domains.

> In this version, the zone tools only read. Record changes, snapshot
> creation and restore, and the "DNS zone" screen of the MCP App come in the
> next sub-batches of issue #6.

## From the conversation

Ask your assistant, for example "list the DNS records of example.com", "show
the MX records of example.com" or "which snapshots does the zone of
example.com have". It uses the `livedns_*` tools (see the
`gandi-mcp-manage-dns` skill):

- **domains**: `livedns_domains` lists the domains whose zone LiveDNS serves;
  `livedns_domain` tells whether the automatic snapshots of a zone are on;
- **records**: `livedns_records` lists them page by page, optionally of one
  type (`A`, `MX`, `TXT`...); `livedns_name_records` gives every record of one
  name, and `livedns_record` one name and type. A record name is relative to
  the zone: `@` for the domain itself, `www`, `*.dev`, `_dmarc`;
- **nameservers**: `livedns_nameservers` gives the nameservers of the zone;
  `livedns_public_nameservers` computes those LiveDNS would give any domain,
  even without an account;
- **snapshots**: `livedns_snapshots` lists the saved copies of a zone, newest
  first, and `livedns_snapshot` shows one with its records;
- **signing keys**: `livedns_signing_keys` and `livedns_signing_key` show the
  keys LiveDNS signs the zone with. The DNSSEC keys published at the registry
  are given by `domain_dnssec_keys` (see [manage your domains](manage-domains.md)).

Record values come from Gandi and may hold anything: they are shown to the
model as untrusted data. A value longer than the free input limit (DKIM keys,
long TXT records) is withheld from the model; export the zone to read it (see
[export a zone](export-and-import-a-zone.md)).

## When something fails

- "This record name or type is not valid": give a name relative to the zone,
  without the domain and without a trailing dot, and a type such as `A`.
- "Gandi did not find this resource": the domain is not served by LiveDNS for
  this account, or the record does not exist. Check `livedns_domains`, and
  switch the domain to LiveDNS with `domain_livedns_enable` if needed.

See the `gandi-mcp-troubleshoot` skill for the other errors.
