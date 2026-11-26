<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 3. Preferences and secrets storage

- Status: accepted
- Date: 2026-11-26
- Issue: #4

## Context

The personal mode keeps, on the user's computer, the configured accounts and
their Gandi Personal Access Tokens. ADR 1 forbids storing Gandi data locally;
only the tokens and the account settings are kept. A token grants API rights
on the user's Gandi organization and must never reach a file in clear, a log,
a tool result or the model.

## Decision

- **Secrets**: tokens are kept in the operating system keyring through
  `keyring` (Windows Credential Manager, macOS Keychain, Secret Service on
  Linux), service `gandi-mcp`, under an opaque key per account (a random
  identifier recorded in the preferences), so that renaming an account does not
  touch the keyring. Keyring calls run in a worker thread because they may
  block on an unlock prompt.
- **No plaintext fallback**: without a usable keyring, operations fail with
  `SecretStoreUnavailableError` and a remedy (install or unlock a keyring).
- **Token value object**: `PersonalAccessToken` validates the format (printable
  ASCII without whitespace, 16 to 512 characters), masks its `repr` and `str`,
  refuses serialization and only exposes the value through `reveal()`.
- **Preferences**: a JSON file without any secret (accounts with their name,
  environment, read-only flag and secret key; the default account), in the
  user configuration directory of the OS (`platformdirs`), path configurable
  with `preferences.path`. Writes are atomic (temporary file in the same
  directory, then replace) and the file carries a format version. A corrupted
  or newer file is refused and never overwritten.

## Alternatives considered

- **Encrypted file for secrets**: works without a keyring, but needs a master
  password or a key stored next to the file. Deferred.
- **TOML preferences**: consistent with the configuration file, but writing
  TOML needs a new dependency (`tomli-w`).
- **SQLite preferences**: transactions and migrations, oversized for a handful
  of accounts and harder to inspect.

## Consequences

- Headless Linux systems need a Secret Service (for example GNOME Keyring or
  KeePassXC) before adding an account; the install and troubleshoot skills
  explain it.
- Uninstalling removes each account (and thus its token) before deleting the
  preferences file.
