---
name: gandi-mcp-report-issue
description: Help a gandi-mcp user report a bug, propose a feature or start contributing. Gathers version, steps and sanitized logs, then opens the GitHub issue after confirmation, or guides to forking and cloning. Use when the user wants to report a problem, suggest an improvement or contribute to gandi-mcp.
---

# Report an issue or start contributing

1. Identify the request: bug, feature or code contribution. For a security
   vulnerability, stop and point to the private report form:
   <https://github.com/bobyone/gandi-mcp/security/advisories/new>.
2. Gather what the template needs:
   - bug: `gandi-mcp --version`, operating system and client, steps to
     reproduce, expected and actual behavior, log excerpts;
   - feature: goal, acceptance criteria, Gandi API endpoints concerned.
3. Remove any token, personal data (names, addresses, emails, phone numbers)
   or configuration content from what you collected, and show the final text
   to the user.
4. After the user confirms, open the issue with the forge template
   (`gh issue create --repo bobyone/gandi-mcp --template "Bug report"` or
   `"Feature request"`), or give the user the text and the link
   <https://github.com/bobyone/gandi-mcp/issues/new/choose>.
5. To contribute code: guide the user to `gh repo fork bobyone/gandi-mcp --clone`
   and `uv sync`, then hand over to the repository's `contribute` skill and
   `CONTRIBUTING.md`.
