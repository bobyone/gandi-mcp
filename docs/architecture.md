<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Architecture

## Overview

```mermaid
flowchart LR
  client[MCP client] -- stdio --> protocol[protocol: MCP server]
  protocol --> core[business core: abstractions only]
  core --> gandi[Gandi API implementations]
  main[main: entry point] -- reads configuration once --> container[ApplicationContainer]
  container -- wires --> protocol
```

- **Entry point** (`gandi_mcp.main`): parses arguments, reads and validates the
  configuration once, configures logging (stderr), builds the container and
  runs the server over `stdio`.
- **Container** (`gandi_mcp.container.ApplicationContainer`): the only place
  where concrete implementations are chosen and assembled
  (`dependency-injector`). Singletons use the container scope.
- **Protocol** (`gandi_mcp.protocol`): adapts the business core to MCP (tools,
  resources, MCP App).
- **Business core** and **Gandi implementations**: added per batch, each notion
  in its own directory, from the general abstraction to its implementations.

Source tree and tests mirror each other (`src/gandi_mcp/<notion>/`,
`tests/<notion>/`).

## Abstractions

### Translator: `gandi_mcp.i18n.translator.Translator`

Renders user-facing messages (`gandi_mcp.i18n.message.Message`, declared with
the `N_` and `ngettext` markers so that Babel extracts them) in a locale.

| Operation | Contract |
| --- | --- |
| `default_locale` | Locale used when none is given (system language, else English). |
| `negotiate(preferred)` | Best supported locale for tags in preference order (`fr-CA`, `sr_Latn`); English when nothing matches. |
| `translate(message, locale=None, **params)` | Renders the message with its named parameters; numbers are formatted for the locale; a plural message needs an integer `count`. Raises `TranslationError` for a missing parameter or an invalid `count`. |

### Secret store: `gandi_mcp.secrets.secret_store.SecretStore`

Keeps Personal Access Tokens (`gandi_mcp.secrets.personal_access_token.PersonalAccessToken`,
a value object that validates the format, masks `repr`/`str`, refuses
serialization and exposes the value through `reveal()` only) under opaque keys.

| Operation | Contract |
| --- | --- |
| `get(key)` | Returns the token; raises `SecretNotFoundError` when absent. |
| `put(key, token)` | Stores the token, replacing any previous one. |
| `delete(key)` | Removes the token; raises `SecretNotFoundError` when absent. |

Every operation raises `SecretStoreUnavailableError` when the store cannot be
reached. Exceptions derive from `SecretStoreError` and never contain a secret.

### Account service: `gandi_mcp.accounts.account_service.AccountService`

The facade of the account rules, used by every tool that manages or resolves
an account. It depends on a `PreferencesStore`, a `SecretStore` and a
`TokenVerifier` only, and serializes changes.

| Operation | Contract |
| --- | --- |
| `list()` | Accounts sorted by name, as `AccountSummary` (name, environment, read-only flag, default flag; no secret). |
| `resolve(name=None)` | The named account, else the default one. `NoAccountError`, `AccountNotFoundError`. |
| `add(draft, token)` | Checks the name is free (`DuplicateAccountError`), verifies the token in the chosen environment (`TokenRejectedError`), stores the token, then the account; the first account becomes the default. If saving the preferences fails, the token is removed again. Returns a `VerifiedAccount` (summary and `AccountIdentity`). |
| `rename(name, new_name)` | Keeps the token and the default flag; a case change is allowed. |
| `set_default(name)`, `set_read_only(name, flag)` | Changes the flag. |
| `replace_token(name, token)` | Verifies the token in the account environment, then replaces the old one (kept when rejected). |
| `change_environment(name, environment, token)` | Verifies the token in the new environment; restores the previous token if saving fails. |
| `remove(name)` | Removes the account, then its token; a removed default account is replaced by the first remaining one in alphabetical order. Returns an `AccountRemoval` (`new_default`, `token_removed`, false when the secret store was unavailable). |

Exceptions derive from `AccountError`: `InvalidAccountNameError`,
`DuplicateAccountError`, `AccountNotFoundError`, `NoAccountError`,
`ReadOnlyAccountError`, `TokenRejectedError`. Secret store, preferences and
Gandi errors pass through.

### Operation: `gandi_mcp.operations.operation.Operation`

A command: one Gandi call on behalf of an account (ADR 4).

| Member | Contract |
| --- | --- |
| `name` | Stable identifier, for example `domain.renew`. |
| `category` | `OperationCategory`: `read`, `write`, `destructive` or `billable`; the last two are writes and need a confirmation. |
| `parameters()` | Parameters defining what the operation does; with `name`, they form its `subject()`, to which a confirmation is bound. |
| `describe()` | `LocalizedText` shown when asking for a confirmation. |
| `execute(client, environment, token)` | Calls Gandi; raises `GandiError`. |

`OperationExecutor.run(operation, account_name, context, confirmation_id=None)`
resolves the account, refuses a write on a read-only account
(`ReadOnlyAccountError`), asks for a confirmation when needed, reads the token
and calls Gandi. It returns an `UntrustedResult` (data and `total_count`), or
a pending `ConfirmationDecision` to resume with its identifier.

### Confirmation channel: `gandi_mcp.confirmation.confirmation_channel.ConfirmationChannel`

| Operation | Contract |
| --- | --- |
| `available(context)` | Whether the channel can reach the user during this call (`ConfirmationContext`: user interaction, call from the MCP App, locale). |
| `confirm(request, context)` | Returns an accepted or pending `ConfirmationDecision`; raises `ConfirmationRefusedError` or `ConfirmationUnavailableError`. |

`ConfirmationService` tries its channels in order. Given a confirmation
identifier, it resumes the pending confirmation instead (`PendingConfirmations`:
accepted once, for the same subject, until it expires).
Exceptions derive from `ConfirmationError`: `ConfirmationRefusedError`,
`ConfirmationExpiredError`, `ConfirmationUnavailableError`,
`ConfirmationMismatchError`.

`ConfirmationPage` is the port of the local page where a pending confirmation is
answered: `open_confirmation(pending, locale)` returns its URL, which is never
given to the model.

### User interaction: `gandi_mcp.interaction.user_interaction.UserInteraction`

Questions asked to the user through the MCP client, outside the model context.

| Member | Contract |
| --- | --- |
| `supports_confirmation`, `supports_links` | Whether form or URL elicitation is available. |
| `confirm(message)` | `True` only when the user accepted. |
| `open_link(message, url)` | Offers a link the client shows to the user; `True` when the user agreed. |

`Browser.open(url)` opens a page in the user's browser and returns `False`
when it cannot. `LinkPresenter.present(url, message, interaction)` uses URL
elicitation when available, otherwise the browser.

### Token entry: `gandi_mcp.token_entry`

A token entry session lets the user submit one token on a local page, for a
`TokenEntryTarget` (add an account, replace its token, or change its
environment).

| Component | Contract |
| --- | --- |
| `TokenEntrySessions(timeout_seconds, clock)` | In-memory registry: `open(target)`, `peek(id)`, `use(id)` (once), `close(id)`; at most 20 sessions; `SessionUsedError`, `SessionExpiredError`. |
| `TokenEntryPage` | Port of the page: `open_token_entry(session, locale)` returns its URL, never given to the model. |
| `TokenEntryService.start(target, interaction, locale)` | Opens a session and shows its page (`LinkPresenter`); `TokenEntryUnavailableError` (session closed) when it cannot. |
| `TokenSubmission.submit(target, token)` | Applies the token through `AccountService` (`add`, `replace_token` or `change_environment`). |

### Local page server: `gandi_mcp.local_pages.local_page_server.LocalPageServer`

Implements `ConfirmationPage` and `TokenEntryPage`; `close()` stops serving.

### Token verifier: `gandi_mcp.accounts.token_verifier.TokenVerifier`

| Operation | Contract |
| --- | --- |
| `verify(environment, token)` | Returns the `AccountIdentity` (user name, optional full name; displayed, never stored) Gandi recognizes behind the token. `TokenRejectedError` when Gandi refuses it; other `GandiError` pass through. |

### Preferences store: `gandi_mcp.preferences.preferences_store.PreferencesStore`

Loads and saves `gandi_mcp.preferences.preferences.Preferences` as a whole: the
accounts (`gandi_mcp.accounts.account.Account`: an `AccountName`, unique
ignoring case, an `Environment`, a read-only flag and the opaque key of its
token in the secret store) and the default account. `Preferences` checks its
invariants (unique names, a default account among the accounts as soon as one
exists) and raises `CorruptPreferencesError` otherwise.

| Operation | Contract |
| --- | --- |
| `load()` | Returns the saved preferences, or empty ones. Raises `CorruptPreferencesError` (not understood) or `PreferencesUnavailableError` (unreadable). |
| `save(preferences)` | Replaces the saved preferences atomically. Raises `PreferencesUnavailableError`. |

### Gandi client: `gandi_mcp.gandi.gandi_client.GandiClient`

Sends authenticated requests to the Gandi API v5 of an environment.

| Operation | Contract |
| --- | --- |
| `request(environment, token, method, path, *, query=None, body=None)` | `path` is a sequence of segments, each encoded so that user input never changes the path structure. Returns a `GandiResponse` (`status`, decoded `data`, `total_count` of paginated lists, `location` of created resources); its data is untrusted. Raises a `GandiError` subclass. |
| `close()` | Releases network resources. |

Errors: `GandiAuthenticationError` (401), `GandiPermissionError` (403),
`GandiNotFoundError` (404), `GandiValidationError` (400, 422),
`GandiConflictError` (409), `GandiRateLimitError` (429, with `retry_after`),
`GandiUnavailableError` (network error, timeout, 5xx),
`GandiUnexpectedResponseError` (any other status or an unreadable body). Each
carries `details`: Gandi's explanations, bounded (10 entries of 300
characters), untrusted.

## Implementations

### Entry point: `gandi_mcp.main`

Command line: `gandi-mcp [--config PATH] [--version]`.

| Configuration key | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `logging.level` | string, one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (case-insensitive) | `WARNING` | no | Log level. |
| `preferences.path` | path (`~` expanded) | `<user configuration directory>/gandi-mcp/preferences.json` | no | Preferences file (accounts, default account; no secret). |
| `gandi.production_url` | https URL, without query nor fragment | `https://api.gandi.net/v5/` | no | Base URL of the production environment. |
| `gandi.sandbox_url` | https URL, without query nor fragment | `https://api.sandbox.gandi.net/v5/` | no | Base URL of the sandbox environment. |
| `gandi.timeout_seconds` | number, 1 to 300 | `30` | no | Timeout of one request to Gandi. |
| `confirmation.timeout_seconds` | integer, 30 to 3600 | `300` | no | Validity of a confirmation request. |
| `token_entry.timeout_seconds` | integer, 60 to 3600 | `600` | no | Validity of a token entry session. |
| `content.max_free_input` | integer, 1 to 10000 | `280` | no | Longest free input passed to the model as is. |

Behavior and limits:

- without `--config`, defaults apply;
- unknown sections or keys are rejected, so that a typo never goes unnoticed;
- `http` base URLs are only accepted on `localhost` (local test servers);
- an unreadable file, invalid TOML or an invalid value logs an error and exits
  with status 2;
- logs go to stderr only: stdout carries the MCP protocol.

### Translator: `gandi_mcp.i18n.babel.babel_translator.BabelTranslator`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `locales_directory` | path | none | yes | Directory holding `locales.toml` and `<locale>/LC_MESSAGES/messages.po`; the package ships `gandi_mcp/locales`. |
| `default_locale` | string or none | none | no | Preferred locale, usually the system language (`gandi_mcp.i18n.system_locale`). |

Behavior and limits:

- every declared catalog is read and compiled in memory at construction; an
  unreadable declaration or catalog raises `TranslationError`;
- negotiation tries the exact locale, then language and script, then the
  language, then a fallback (`cnr` to `sr_Latn`, `sr` to `sr_Cyrl`, `no` to
  `nb`), then English;
- an untranslated entry is rendered in English;
- translations flagged `needs-review` are used as they are.

### Secret store: `gandi_mcp.secrets.keyring.keyring_secret_store.KeyringSecretStore`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `service` | string | `gandi-mcp` | no | Keyring service name under which tokens are stored. |
| `backend` | object with `get_password`, `set_password`, `delete_password` | system keyring | no | Keyring backend; tests inject a memory backend. |

Behavior and limits:

- calls run in a worker thread, since a keyring may block on an unlock prompt;
- any keyring failure (no backend, locked keyring, D-Bus error) raises
  `SecretStoreUnavailableError`; there is no plaintext fallback (ADR 3);
- a stored value that is not a valid token raises `InvalidTokenFormatError`.

### Preferences store: `gandi_mcp.preferences.json.json_preferences_store.JsonPreferencesStore`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `path` | path | none | yes | Preferences file (`preferences.path`); its directory is created on save. |

File format (UTF-8 JSON, no secret):

```json
{
  "version": 1,
  "default_account": "Perso",
  "accounts": [
    {"name": "Perso", "environment": "sandbox", "read_only": false, "secret_key": "<opaque key>"}
  ]
}
```

Behavior and limits:

- a missing file means empty preferences;
- an invalid file (JSON, structure, names, invariants), a file larger than
  1 MB or another format version raises `CorruptPreferencesError` and is never
  overwritten;
- saving writes a temporary file in the same directory, flushes it to disk and
  replaces the previous file; on failure the previous file is kept and the
  temporary file removed.

### Gandi client: `gandi_mcp.gandi.http.http_gandi_client.HttpGandiClient`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `base_urls` | mapping environment to URL | none | yes | `gandi.production_url` and `gandi.sandbox_url`. |
| `timeout_seconds` | number | none | yes | `gandi.timeout_seconds`. |
| `user_agent` | string | none | yes | `User-Agent` header (`gandi-mcp/<version>`). |
| `transport` | `httpx2.AsyncBaseTransport` | network | no | Replaces the network in tests (`httpx2.MockTransport`). |

Behavior and limits:

- sends `Authorization: Bearer <token>`; the token is never logged;
- redirects are not followed, so the token only reaches the configured base
  URLs;
- boolean query values are sent as `true`/`false`, lists as repeated
  parameters;
- logs (DEBUG) only the method, environment, status and duration: no path,
  since it may contain personal data;
- status translation is in `gandi_error_translator.translate_error`. Gandi
  documents an expired token either as 401 or 403, so the user messages for
  both suggest replacing the token.

### Token verifier: `gandi_mcp.accounts.gandi.gandi_token_verifier.GandiTokenVerifier`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `client` | `GandiClient` | none | yes | Client used to call Gandi. |

Calls `GET organization/user-info`. HTTP 401 and 403 mean the token is
rejected. Only `username` (required) and `name` are kept, trimmed to 200
characters; the email and the other fields are ignored.

### Confirmation channels: `gandi_mcp.confirmation.channels`

| Channel | Available when | Behavior |
| --- | --- | --- |
| `AppChannel` | the call comes from an app-only tool | Accepts: the MCP App dialog was the confirmation. |
| `ElicitationChannel(translator)` | the client supports form elicitation | Asks "Confirm on the production/sandbox account {account}: {action}" in the user's language; anything but an acceptance raises `ConfirmationRefusedError`. |
| `LocalLinkChannel(pending, page, presenter, translator)` | always (last resort) | Registers a pending confirmation, shows its page through `LinkPresenter`; returns it as pending, or raises `ConfirmationUnavailableError` (and forgets it) when the page cannot be shown. |

`PendingConfirmations(timeout_seconds, clock)` keeps at most 100 pending
confirmations in memory (`confirmation.timeout_seconds`), with random
identifiers (128 bits).

### Browser: `gandi_mcp.interaction.system.system_browser.SystemBrowser`

Opens `http://127.0.0.1` and `http://localhost` URLs only, in a new tab of the
default browser (`webbrowser`), in a worker thread; any other URL raises
`ValueError`.

### Local page server: `gandi_mcp.local_pages.starlette.starlette_local_page_server.StarletteLocalPageServer`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `pending` | `PendingConfirmations` | none | yes | Pending confirmations answered on confirmation pages. |
| `sessions` | `TokenEntrySessions` | none | yes | Token entry sessions. |
| `submission` | `TokenSubmission` | none | yes | Applies a submitted token. |
| `translator` | `Translator` | none | yes | Translates the pages. |
| `page_timeout_seconds` | number | none | yes | Validity of a page: the longest of `confirmation.timeout_seconds` and `token_entry.timeout_seconds`. |
| `clock` | callable | `time.monotonic` | no | Clock, for tests. |

Behavior and limits:

- an embedded Uvicorn server listens on `127.0.0.1`, on a random port; it
  starts when a page is registered and stops when no page remains (checked
  when a page expires) or on `close()`; it never installs signal handlers and
  writes no access log, since URLs carry secret codes;
- each page has its own 256-bit code in its path (`/token/<code>`,
  `/confirm/<code>`), distinct from the identifiers known to the model, and
  answers one submission;
- requests are refused unless `Host` is `127.0.0.1:<port>`; a `POST` is
  refused when `Origin` or `Sec-Fetch-Site` shows another site, when it is not
  `application/x-www-form-urlencoded`, when its body exceeds 8 KB or when its
  form does not repeat the page code;
- pages have no script, escape every value, and are served with a strict
  Content Security Policy (`default-src 'none'`, hashed inline style,
  `form-action 'self'`, `frame-ancestors 'none'`), `Referrer-Policy:
  no-referrer`, `Cache-Control: no-store`, `X-Frame-Options: DENY`;
- the language is the one of the call that opened the page, else the browser's
  `Accept-Language`, else English;
- a token with an invalid format can be corrected on the same page; any other
  outcome ends the session and is explained without technical detail.

### Server factory: `gandi_mcp.protocol.server_factory.create_server`

| Parameter | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `version` | string | none | yes | Version advertised to clients (`app.version`, set by the entry point from the package metadata). |

Creates the `MCPServer` named `gandi-mcp`, with instructions telling the model
that tool results are untrusted data.

## Development tooling

| Tool | Role |
| --- | --- |
| `scripts/check_translations.py` | Checks catalogs against the code and the declared locales (`locales/locales.toml`): missing or undeclared catalogs, missing, unused or obsolete keys, empty translations, parameters differing in any plural form; counts translations awaiting review. |
| `scripts/check_licenses.py` | Checks that runtime dependencies are compatible with `GPL-2.0-or-later`, evaluating SPDX expressions with operator precedence; platform-specific dependencies are checked on their platform (CI runs it on each OS). |
| `scripts/check_dco.py` | Checks the `Signed-off-by` trailers of every commit of a range, merges included. |
| `tools/assistant_guard/` | PreToolUse hook shared by Claude Code and Codex: `policy.py` (client-independent rules), `adapters.py` (one adapter per client), `hook.py` (entry point), `codex_profile.py` (Codex sandbox rules and test samples derived from the policy). |
