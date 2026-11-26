<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Add a Gandi operation

Each call to Gandi is an `Operation` (a command, see
[ADR 4](../decisions/0004-confirmation-channels.md)). The `OperationExecutor`
applies the common rules, so an operation only describes itself and calls
Gandi.

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

    async def execute(self, client, environment, token) -> GandiResponse:
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
