// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId } from "react";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import { useTranslation } from "react-i18next";
import {
  CONTACT_FIELDS,
  CONTACT_TYPES,
  type ContactDraft,
  type ContactField,
  type ContactType,
} from "../../api/domain";

export interface ContactFormProps {
  readonly contact: ContactDraft;
  readonly invalid: ReadonlySet<ContactField>;
  /** Show the invalid fields, once the user tried to submit. */
  readonly validated: boolean;
  readonly onChange: (contact: ContactDraft) => void;
}

const INPUT_TYPES: Partial<Record<ContactField, string>> = { email: "email", phone: "tel" };
const AUTOCOMPLETE: Record<ContactField, string> = {
  orgname: "organization",
  given: "given-name",
  family: "family-name",
  email: "email",
  phone: "tel",
  streetaddr: "street-address",
  zip: "postal-code",
  city: "address-level2",
  country: "country",
};

/** Fields of a domain contact typed in the App; never sent to the model. */
export function ContactForm({ contact, invalid, validated, onChange }: ContactFormProps) {
  const { t } = useTranslation();
  const help = (field: ContactField): string | null =>
    field === "phone"
      ? t("contact.phone.help")
      : field === "country"
        ? t("contact.country.help")
        : null;
  const problem = (field: ContactField): string =>
    field === "email"
      ? t("validation.contact.email")
      : field === "phone"
        ? t("validation.contact.phone")
        : field === "country"
          ? t("validation.contact.country")
          : field === "orgname"
            ? t("validation.contact.orgname")
            : t("validation.required");
  const id = useId();
  const fields = CONTACT_FIELDS.filter(
    (field) => field !== "orgname" || contact.type !== "individual",
  );
  return (
    <fieldset>
      <legend className="h6">{t("role.owner")}</legend>
      <p className="text-body-secondary small">{t("dialog.register.ownerHelp")}</p>
      <Form.Group controlId={`${id}-type`} className="mb-2">
        <Form.Label>{t("contact.type")}</Form.Label>
        <Form.Select
          value={contact.type}
          onChange={(event) => {
            onChange({ ...contact, type: event.target.value as ContactType });
          }}
        >
          {CONTACT_TYPES.map((type) => (
            <option key={type} value={type}>
              {t(`contact.type.${type}`)}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
      <Row xs={1} sm={2} className="g-2">
        {fields.map((field) => {
          const helpText = help(field);
          return (
            <Col key={field}>
              <Form.Group controlId={`${id}-${field}`}>
                <Form.Label>{t(`contact.${field}`)}</Form.Label>
                <Form.Control
                  type={INPUT_TYPES[field] ?? "text"}
                  autoComplete={AUTOCOMPLETE[field]}
                  value={contact[field]}
                  maxLength={field === "country" ? 2 : 255}
                  required={field !== "phone"}
                  isInvalid={validated && invalid.has(field)}
                  aria-describedby={helpText ? `${id}-${field}-help` : undefined}
                  onChange={(event) => {
                    onChange({ ...contact, [field]: event.target.value });
                  }}
                />
                {helpText && (
                  <Form.Text id={`${id}-${field}-help`} className="d-block">
                    {helpText}
                  </Form.Text>
                )}
                <Form.Control.Feedback type="invalid">{problem(field)}</Form.Control.Feedback>
              </Form.Group>
            </Col>
          );
        })}
      </Row>
    </fieldset>
  );
}
