<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Set up zone transfers to a secondary server

A secondary DNS server of yours can copy a LiveDNS zone (zone transfer,
AXFR). LiveDNS lets it do so from the IP addresses you allow, authenticated by
a TSIG key.

> In this version, the zone transfer tools only read. Adding a secondary
> server, creating or associating a TSIG key come in the next sub-batch of
> issue #6.

## Check the current settings

Ask your assistant, for example "which secondary servers can transfer the
zone of example.com" or "list my TSIG keys". It uses the `livedns_*` tools
(see the `gandi-mcp-zone-transfer` skill):

- `livedns_secondary_servers`: the IP addresses allowed to transfer a zone;
- `livedns_tsig_keys` and `livedns_tsig_key`: the TSIG keys of the account;
- `livedns_domain_tsig_keys`: the keys associated with a zone.

The secret of a TSIG key is never shown in the conversation: it appears as
`hidden`.

## Configure the secondary server

Ask for the configuration of your server software: "give me the bind
configuration of my TSIG key". `livedns_tsig_config` supports `bind`, `knot`,
`nsd` and `powerdns`:

- without a file, the assistant gets the sample with its secret replaced by
  `<hidden>`, to explain it;
- with a file, for example "write it to tsig/bind.conf", the full sample,
  secret included, is written to the work directory (see
  [export a zone](export-and-import-a-zone.md) for its location). The file is
  readable by you only on macOS and Linux; on Windows, it keeps the
  permissions of your user profile. Copy it to your server over a secure
  channel, then delete it.
