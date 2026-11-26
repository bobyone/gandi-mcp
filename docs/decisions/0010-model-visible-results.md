<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# 10. Personal data and long texts in results sent to the model

- Status: accepted
- Date: 2026-11-26
- Issue: #5
- Supersedes: [ADR 9](0009-contact-minimization.md)

## Context

ADR 9 only summarized contacts found under `owner`, `admin`, `bill` and
`tech`. The review of the first domain tools found personal data elsewhere in
documented responses: email addresses in the owner change parameters
(`new_owner_email`...) and in the form of authorization answers (`foa`),
names, addresses and emails of trademark claim `contacts` and `holders`, and
the owner's name (`domain_owner`) in domain lists. Claims also carry
`goods_and_services`, a very long free text. The project rules forbid passing
external free text longer than `content.max_free_input` (280 characters by
default) to the model as is.

## Decision

- `ContactRedactor` detects personal data by its shape, at any depth and
  whatever the key:
  - a mapping under a contact role, an item of a `contacts` or `holders`
    list (trademark claims, whose fields are all optional), a mapping carrying
    an address, name or phone field (`streetaddr`, `street`, `given`,
    `family`, `phone`, `mobile`, `fax`, `city`, `zip`, `pc`), or a `name` next
    to an `email`, is a contact, reduced to `type`, `country`, `cc`,
    `same_as_owner` and `details: "hidden"`;
  - a text field whose name ends with `email`, or `domain_owner`, becomes
    `"hidden"`;
  - `authinfo` becomes `"hidden"`.

  The opt-ins of ADR 9 (`include_contact_details`,
  `include_authorization_code`) are kept, on the tools that offer them.
- `LongTextFilter` then replaces every text longer than
  `content.max_free_input` by `{"withheld": "long_text", "length": n}`: the
  text is used only in the interface (the MCP App), never sent to the model.
  Technical values that are long by nature (`public_key`, `digest`) are kept
  when they only contain base64 or hexadecimal characters.
- Both apply to every domain read tool, through `DomainToolRunner`. The
  same limit applies to the details of Gandi errors: `ErrorPresenter` replaces
  a longer detail by a notice of its length.

## Alternatives considered

- **Endpoint-specific allowlists** of the fields the model may see: the
  strictest, but 22 response schemas (and many more in the next APIs) to
  maintain by hand; a field Gandi adds is silently dropped, and the
  documentation does not describe every shape. Shape-based detection covers
  new endpoints and new fields that follow Gandi's naming.
- **Truncating long texts**: still sends the beginning of an external text,
  which may carry an injection.
- **Summarizing long texts with an intermediate model**: allowed by the rules,
  but needs a local model and a strict schema; postponed until a tool needs
  the content of such a text.

## Consequences

- A personal field named outside these conventions would pass: new endpoints
  add their documented shapes to the regression tests.
- The model knows a long text exists and its length, and can tell the user to
  read it in the MCP App or at Gandi.
