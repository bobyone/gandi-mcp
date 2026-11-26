---
name: gandi-mcp-manage-accounts
description: Add, rename, lock, set as default, re-authenticate, move between production and sandbox, or remove the Gandi accounts used by gandi-mcp. Use when the user wants to connect a Gandi account, replace an expired Personal Access Token, switch an account to the sandbox, make an account read-only or remove an account.
---

# Manage gandi-mcp accounts

Use the gandi-mcp tools; never reimplement them, never read the preferences file
or the keyring yourself.

**Never ask the user for a Personal Access Token in the conversation, and never
pass one to a tool.** The tools show the user a page (in the client, the MCP App
or their browser) where they type it.

1. List the accounts with `list_accounts` before any change.
2. Add an account with `add_account` (name, `environment`, optional
   `read_only`):
   - suggest `sandbox` first for tests: the sandbox token is created at
     <https://admin.sandbox.gandi.net/>, the production one at
     <https://admin.gandi.net/> (organization settings, Personal Access
     Tokens);
   - tell the user a page opened for the token, wait until they say it is
     done, then call `list_accounts` to check.
3. Change an account with `update_account`: `new_name`, `make_default`,
   `read_only`. Turning `read_only` off asks the user to confirm.
4. Replace an expired or revoked token with `replace_account_token`; move an
   account between environments with `change_account_environment` (it needs a
   token valid in the new environment).
5. Remove an account with `remove_account`. The user confirms outside the
   conversation. If the result is `confirmation_pending`, wait until the user
   says they answered on the page, then call `remove_account` again with the
   same name and the returned `confirmation_id`. Never invent an identifier.
   An account listed with `removal_pending: true` had its removal interrupted:
   remove it again to finish.
6. If a tool fails, relay its message: it says what happened and how to fix
   it. For keyring or browser problems, use the `gandi-mcp-troubleshoot`
   skill.
