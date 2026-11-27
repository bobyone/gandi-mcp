---
name: gandi-mcp-privacy
description: Answer questions about the personal data gandi-mcp processes, its purposes, recipients, retention and the user's rights, and guide the user to exercise them. Use when the user asks what gandi-mcp does with their data or tokens, or wants their data removed.
---

# Privacy questions about gandi-mcp

Answer only from these documents, and cite them:

- [records of processing](../../docs/privacy/records-of-processing.md);
- [privacy policy](../../docs/privacy/privacy-policy.md) (draft; the French
  version is authoritative).

Key facts:

- the software runs locally; its authors receive no data;
- Personal Access Tokens stay in the OS keyring and never reach the model;
  they are typed in the MCP App or on a local page, never in the conversation;
- account settings (name, environment, read-only flag, default account) are
  kept in a local preferences file without secret, and are sent to the model
  when it lists the accounts;
- the Gandi identity behind a token is displayed when it is saved, never
  stored;
- Gandi data is fetched on demand and not stored by the software, except the
  files the user asks to export to the work directory (zone files, TSIG
  samples), kept until the user deletes them; the model only gets their name,
  size and record count;
- DNS record values may hold personal data (an email address in a TXT
  record); long values are withheld from the model;
- the secret of a TSIG key never reaches the model; a file holding it is
  readable by its owner only (macOS, Linux);
- tool results are sent to the provider of the user's AI model.

To exercise rights:

- **remove a token and its account settings**: remove the account with the
  `remove_account` tool (see the `gandi-mcp-manage-accounts` skill); the user
  confirms outside the conversation;
- **exported files**: the user deletes them from the work directory
  (`files.work_directory`, by default `gandi-mcp/files` in the user data
  directory); the software never deletes them;
- **data held by Gandi or by the AI provider**: the user contacts them
  directly; the software keeps no other copy.

Never present these answers as legal advice.
