<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Manage your DNS records

Look up the zones that Gandi LiveDNS serves for your domains, from the
conversation. Try it first with a [sandbox](use-the-sandbox.md) account, if
LiveDNS is available there for your domains.

> Replacing or deleting records, importing a zone, restoring a snapshot and
> the "DNS zone" screen of the MCP App come in the next steps of issue #6.

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
  even one that is not in your account;
- **snapshots**: `livedns_snapshots` lists the saved copies of a zone, newest
  first, and `livedns_snapshot` shows one with its records;
- **signing keys**: `livedns_signing_keys` and `livedns_signing_key` show the
  keys LiveDNS signs the zone with. The DNSSEC keys published at the registry
  are given by `domain_dnssec_keys` (see [manage your domains](manage-domains.md)).

## Add records

- "create an A record www pointing to 192.0.2.1": `livedns_record_create`.
  If the record exists with the same values, nothing changes; with other
  values, Gandi refuses it.
- "add a TXT value to @": `livedns_record_values_add` keeps the other values.
- Values are written as LiveDNS writes them: `10 mail.example.com.` for an MX,
  TXT values between double quotes. gandi-mcp refuses a value with a control
  character or a newline, a TTL outside 300 to 2592000 seconds, and an A, AAAA,
  CNAME, NS, MX or SRV value of the wrong shape, before asking Gandi.
- "publish the ACME challenge value ... for _acme-challenge":
  `livedns_domain_verification` (TXT or CNAME only; the token needs the domain
  verification permission).
- Snapshots: `livedns_snapshot_create` (optional name), `livedns_snapshot_rename`
  and `livedns_snapshot_delete`, which you confirm outside the conversation.
- Signing keys: `livedns_signing_key_create`, `livedns_signing_key_restore` and
  `livedns_signing_key_delete` (confirmed). Publish the DS record of a new key
  at the registry with `domain_dnssec_keys_replace`, and remove it there before
  deleting the key, or the domain may stop resolving.
- `livedns_domain_add` creates the LiveDNS zone of a domain of your account,
  `livedns_automatic_snapshots_update` turns its automatic snapshots on or off.

A read-only account refuses every change.

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
