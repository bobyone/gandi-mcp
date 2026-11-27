<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Entry points and guarantees

Update this document in the same commit as any code adding, changing or
removing an entry point or a guarantee. Terms come from the
[glossary](../glossary.md).

## Callers

gandi-mcp runs in personal mode only: a local MCP server over `stdio`, started
by the user's MCP client. There are no roles nor tenants: every caller acts for
the local user, on the accounts configured on this computer. Two kinds of
callers are distinguished:

- **the model**, through the MCP client: its arguments are untrusted;
- **the MCP App**, rendered by the client: it calls app-only tools and the
  model tools listed in `APP_CALLED_TOOLS` (ADR 12); its results never reach the
  model.

The local pages are served on `127.0.0.1` to the user's browser, behind a
single-use random code that is never given to the model.

## Entry points

Controls common to every Gandi operation (`operations/operation_executor.py`
`OperationExecutor.run`): resolve the account, refuse a write on a read-only
account, ask for a confirmation outside the model for destructive operations
and operations needing a secret input, check again that the account is still
writable right before the request. Billable operations go through
`operations/order_executor.py` `OrderExecutor.run` (quote, dry run,
price-bound confirmation, price re-check). Results shown to the model go
through the result filters (`protocol/tools/endpoint_tool_runner.py`
`filtered`: `ContactRedactor`, `SecretFieldFilter`, then `LongTextFilter`).
Files are only written in the work directory (`files/local/local_work_directory.py`
`LocalWorkDirectory`: relative path, confined after resolution, no overwrite
unless asked), through `operations/text_file_exporter.py` `TextFileExporter.export`.

| Entry point | Caller | Control |
| --- | --- | --- |
| `domain_*` read tools (22) | model, App | `OperationExecutor.run`; filters in `EndpointToolRunner.read` |
| `domain_*` write tools, not confirmed (16) | model, App | `OperationExecutor.run` (read-only refusal); `EndpointToolRunner.write` |
| `domain_*` destructive tools (17) | model, App | `OperationExecutor.run` (confirmation bound to operation, parameters, account and environment) |
| `domain_transfer_in_code_update`, `domain_transfer_out_decline` (writes), `domain_transfer_out_accept` (destructive, also counted above) | model, App | `OperationExecutor.run` (always confirmed; the authorization code is typed on the local confirmation page, never passed by the model, ADR 11) |
| other `livedns_*` read tools (14) | model, App | `OperationExecutor.run`; filters in `EndpointToolRunner.read`; `livedns_record`, `livedns_name_records`, `livedns_records`: `livedns/record_name.py` `RecordName`, `livedns/record_type.py` `RecordType` |
| `livedns_tsig_keys`, `livedns_tsig_key`, `livedns_tsig_config` (without `file`) | model, App | `OperationExecutor.run`; `content/secret_field_filter.py` `SecretFieldFilter` hides the key secret, also inside the sample (`operations/livedns/tsig_configuration.py`) |
| `livedns_zone_export`, `livedns_snapshot_export`, `livedns_tsig_config` (with `file`) | model, App | `TextFileExporter.export`: target checked before the Gandi call, `LocalWorkDirectory` confinement, private file for a TSIG sample; only the file name, size and record count are returned |
| `domain_register`, `domain_renew`, `domain_restore`, `domain_transfer_in` | model, App | `OrderExecutor.run` (`protocol/tools/domains/domain_order_runner.py`) |
| `list_accounts`, `list_organizations` | model, App | `protocol/tools/accounts_tools.py`, `organization_tools.py`: no secret in results |
| `add_account`, `replace_account_token`, `change_account_environment` | model | `accounts_tools.py`: the token is typed on a local page (token entry session), never passed by the model |
| `update_account`, `set_paying_organization` | model, App | `accounts_tools.py`, `organization_tools.py`; allowing writes on a read-only account is confirmed |
| `remove_account` | model | `accounts_tools.py`: confirmed |
| `open_gandi_app` | model, App | `protocol/app/accounts_app_tools.py`: read-only |
| `app_*` tools (6) | App only | `accounts_app_tools.py`: refused unless the client supports MCP Apps (`client_supports_apps`); confirmations still asked by the server |
| `GET`/`POST /token/{code}` | user's browser | `local_pages/starlette/starlette_local_page_server.py` `_token`: local address, single-use code, form origin and size checks |
| `GET`/`POST /confirm/{code}` | user's browser | `starlette_local_page_server.py` `_confirmation`: same checks; untrusted data escaped |

## Guarantees

| Guarantee | Test trying to violate it |
| --- | --- |
| A read-only account never changes anything at Gandi. | `tests/operations/test_operation_executor.py::test_write_operations_refused_on_a_read_only_account`, `tests/protocol/tools/domains/test_domain_write_tools.py::test_writes_are_refused_on_a_read_only_account`, `tests/operations/test_order_executor.py::test_read_only_accounts_never_buy` |
| An account made read-only while a write waits does not change anything. | `test_operation_executor.py::test_a_read_only_toggle_during_the_token_read_stops_the_write`, `test_order_executor.py::test_a_read_only_toggle_during_the_last_token_read_does_not_buy` |
| A destructive operation runs only after the user's confirmation, given outside the model. | `test_operation_executor.py::test_refused_confirmation_has_no_effect`, `test_domain_write_tools.py::test_risky_changes_wait_for_the_confirmation`, `tests/protocol/app/test_accounts_app_tools.py::test_an_app_call_alone_never_confirms` |
| A confirmation is valid once, for the same operation, parameters, account and environment. | `tests/confirmation/test_pending_confirmations.py::test_confirmation_for_another_operation`, `::test_accepted_confirmation_is_used_once`, `test_operation_executor.py::test_a_confirmation_is_bound_to_the_account_environment`, `tests/protocol/tools/test_accounts_tools.py::test_invented_or_reused_confirmation_is_refused` |
| An order is placed only at the price the user confirmed. | `test_order_executor.py::test_a_price_change_cancels_the_order`, `::test_a_new_price_does_not_match_the_confirmation` |
| A Personal Access Token never reaches the model nor the logs. | `test_accounts_tools.py::test_list_accounts_never_shows_secrets`, `tests/accounts/test_account_service.py::test_list_is_sorted_and_secret_free` |
| An authorization code typed by the user never reaches the model. | `test_order_executor.py::test_a_transfer_never_echoes_its_code`, `::test_a_refused_transfer_never_echoes_its_code`, `test_domain_write_tools.py::test_a_typed_code_is_never_echoed_to_the_model` |
| Domain contacts reach the model only as type and country, unless the user asks for details. | `tests/protocol/tools/domains/test_domain_tools.py::test_contacts_and_authorization_code_are_hidden_by_default`, `tests/domains/contacts/test_contact_redactor.py::test_contacts_are_found_at_any_depth_and_in_lists` |
| A long Gandi text never reaches the model. | `test_domain_tools.py::test_follow_up_and_claims_hide_personal_data_and_long_texts`, `::test_long_gandi_error_details_are_withheld` |
| The secret of a TSIG key never reaches the model, even inside a configuration sample. | `tests/protocol/tools/livedns/test_livedns_read_tools.py::test_tsig_secrets_never_reach_the_model`, `::test_the_full_tsig_sample_goes_to_a_private_file_only`, `tests/content/test_secret_field_filter.py::test_a_secret_repeated_in_a_text_is_hidden` |
| No file is written outside the work directory, and no file is replaced unless the user asked for it. | `tests/files/local/test_local_work_directory.py::test_paths_leading_out_or_not_allowed_are_refused`, `::test_a_symbolic_link_leading_out_is_refused`, `::test_an_existing_file_is_kept_unless_overwriting_is_asked`, `test_livedns_read_tools.py::test_exports_refuse_existing_files_and_paths_out_of_the_directory` |
| A file holding a TSIG secret is readable by its owner only (POSIX). | `test_local_work_directory.py::test_a_private_file_is_readable_by_its_owner_only` |
| The content of an exported file never reaches the model. | `test_livedns_read_tools.py::test_a_zone_is_exported_to_a_file_out_of_the_conversation` |
| User input never changes the structure of a Gandi API path. | `tests/gandi/http/test_http_gandi_client.py::test_encodes_user_input_in_path_segments`, `tests/operations/endpoint/test_endpoint_operation.py::test_refuses_invalid_arguments`, `test_livedns_read_tools.py::test_invalid_record_names_and_types_never_reach_gandi`, `tests/livedns/test_record_name.py::test_invalid_names_are_refused` |
| App-only tools cannot be called outside the MCP App. | `test_accounts_app_tools.py::test_app_tools_are_refused_without_mcp_apps` |
| A local page answers only its single-use code, from the user's browser. | `tests/local_pages/starlette/test_starlette_local_page_server.py::test_untrusted_requests_are_refused`, `::test_unknown_and_expired_pages`, `::test_confirmation_is_answered_once` |
| Untrusted Gandi data shown on a local page cannot inject markup. | `test_starlette_local_page_server.py::test_confirmation_page_escapes_untrusted_data` |
