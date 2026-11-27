<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Add a Gandi operation

Each call to Gandi is an `Operation` (a command, see
[ADR 4](../decisions/0004-confirmation-channels.md)). The `OperationExecutor`
applies the common rules, so an operation only describes itself and calls
Gandi.

## API endpoints: declare them in the catalogue

For an endpoint of a Gandi API, do not write an `Operation` class
([ADR 8](../decisions/0008-endpoint-catalogue.md),
[ADR 13](../decisions/0013-shared-endpoint-catalogue.md)). The steps below use the
Domain API; another API has its own catalogue module and tool directory.

1. Add an `Endpoint` (`gandi_mcp.operations.endpoint.endpoint`) to
   `src/gandi_mcp/operations/domain/domain_endpoints.py`
   (name, method, path with `{placeholder}` segments, category, accepted query
   parameters; a description for confirmed categories) and to the matching
   tuple (`READ_ENDPOINTS` or `WRITE_ENDPOINTS`). Set `supports_dry_run` when
   Gandi accepts `Dry-Run: 1`, and `secret_field` with `secret_label` when the
   user must type a secret (ADR 11). Declare confirmation descriptions with `N_`
   in `operations/domain/domain_messages.py` and translate them.
2. Add the tool function to the domain tool module of its notion
   (`src/gandi_mcp/protocol/tools/domains/`), register it with
   `add_read_tool` or `add_write_tool`, and call `EndpointToolRunner.read` or
   `EndpointToolRunner.write` (give confirmed tools a `confirmation_id`
   parameter). Pass path values and
   query as functions that build the validated values (`DomainName`,
   `HostLabel`, `TldName`).
3. Add its arguments and expected request to `CALLS` in
   `tests/protocol/tools/domains/test_domain_tools.py` (reads) or
   `test_domain_write_tools.py` (writes).

For the LiveDNS API, the catalogue is
`src/gandi_mcp/operations/livedns/livedns_endpoints.py`, the values are in
`gandi_mcp.livedns` (`RecordName`, `RecordType`, identifiers), the tool
modules in `src/gandi_mcp/protocol/tools/livedns/` and the protocol tests in
`tests/protocol/tools/livedns/`. One more option of `Endpoint` matters there:
`accept=MediaType.TEXT` asks Gandi for a zone file instead of JSON; such an
endpoint is exported to the work directory with `ZoneFileService` or
`TextFileExporter` (ADR 15), never returned to the model.

A read made of several calls (`livedns_tsig_config` reads the key, then its
sample) is an `Operation` class, run with `EndpointToolRunner.read_operation`.

The rest of this guide applies to operations that need their own class.

## 1. Write the operation

Create one file per operation in the directory of its notion, for example
`src/gandi_mcp/operations/domain/renew_domain.py`:

```python
class RenewDomain(Operation):
    def __init__(
        self, fqdn: DomainName, years: int
    ) -> None: ...  # validate the parameters here (type, format, bounds)

    @property
    def name(self) -> str:
        return "domain.renew"

    @property
    def category(self) -> OperationCategory:
        return OperationCategory.BILLABLE

    def parameters(self) -> Mapping[str, JsonValue]:
        return {"fqdn": str(self._fqdn), "years": self._years}

    def describe(self) -> LocalizedText:
        return LocalizedText(RENEW_DOMAIN, {"domain": str(self._fqdn), "count": self._years})

    async def execute(self, client, environment, token, answer=None) -> GandiResponse:
        return await client.request(
            environment,
            token,
            "POST",
            ("domain", "domains", str(self._fqdn), "renew"),
            body={"duration": self._years},
        )
```

- Choose the category carefully: `read`, `write`, `destructive` (deletes or
  irreversibly changes) or `billable` (charges the account). Read-only
  accounts refuse every write; destructive and billable operations are
  confirmed by the user.
- `parameters()` must include everything that changes what the operation
  does: a confirmation is only valid for the same name and parameters.
- Pass user input as path **segments**: the client encodes each one.
- A confirmed operation can describe its effect from a read (`prepare`, called
  before the confirmation, never a change) and offer a yes or no choice
  (`confirmation_option()`); `execute` then gets the choice in
  `answer.option_chosen` (ADR 14).
- Declare the description with `N_` or `ngettext` in the module, add it to the
  catalogs (see [Add a language](add-a-language.md)).

## 2. Expose it as a tool

In the `ToolModule` of the notion (`src/gandi_mcp/protocol/tools/`):

1. Declare the tool with `server.add_tool`, an English name and description
   for the model, and its annotations (`readOnlyHint`, `destructiveHint`,
   `idempotentHint`, `openWorldHint`).
2. Build the operation from the arguments, then call
   `executor.run(operation, account, context, confirmation_id)`.
3. Return the `UntrustedResult` data marked as untrusted, or the pending
   confirmation (`status: confirmation_pending`).
4. Turn exceptions into tool errors with the `ErrorPresenter`.

Register the module in `ApplicationContainer` (`tool_modules`).

## 3. Test it

- Unit test of the operation with `FakeGandiClient` (path, method, body,
  category, subject).
- Protocol test with the in-memory MCP client: tool listing, annotations,
  confirmation accepted, refused and pending, read-only refusal.
- Manual test on the [Gandi sandbox](use-the-sandbox.md) only.
