<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Use the Gandi sandbox

The Gandi sandbox (<https://admin.sandbox.gandi.net/>) is a separate test
environment: operations there have no real effect and cost nothing. It has its
own accounts and tokens: a production token does not work in the sandbox, and
the reverse.

Use it to try gandi-mcp, and for every manual test of a contribution.

## Set up

1. Create a sandbox Gandi account at <https://admin.sandbox.gandi.net/> and a
   Personal Access Token there.
2. Add it in gandi-mcp as a `sandbox` account (see
   [Add a Gandi account](add-a-gandi-account.md)), for example named `Tests`.
3. Make it the default account while testing: "make Tests the default
   account" (`update_account` with `make_default`).

Confirmations name the environment ("Confirm on the sandbox account Tests:
..."), so that you always know where an operation applies.

## Limits of the sandbox

According to Gandi, the sandbox offers the Domain, LiveDNS, Billing,
Organization, Mailbox and LinkedZone services; domains can only be registered
in `.com`, `.net`, `.org` and `.fr`, and transfers are not available.

## Move an account to production

Use `change_account_environment` with `production`: gandi-mcp asks for a token
valid in production and checks it with Gandi before switching. The old token
is kept if the new one is refused.

## Point to another sandbox address

The base URLs are configuration keys (`gandi.sandbox_url`,
`gandi.production_url`, see [`gandi-mcp.example.toml`](../../gandi-mcp.example.toml));
`http` is only accepted on `localhost`, for local test servers.
