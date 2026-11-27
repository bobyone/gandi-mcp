// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, useState, type SubmitEvent } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";
import { isValidName, isValidToken, type Environment } from "../../api/account";

export const ADMIN_URLS: Readonly<Record<Environment, string>> = {
  production: "https://admin.gandi.net/",
  sandbox: "https://admin.sandbox.gandi.net/",
};

export interface AccountFormValues {
  readonly name: string;
  readonly environment: Environment;
  readonly readOnly: boolean;
  readonly token: string;
}

export interface AccountFormProps {
  /** Dialog title, already translated. */
  readonly title: string;
  /** Which fields are shown; the token field is always shown. */
  readonly fields: {
    readonly name: boolean;
    readonly environment: boolean;
    readonly readOnly: boolean;
  };
  readonly initial: Omit<AccountFormValues, "token">;
  readonly busy: boolean;
  readonly onSubmit: (values: AccountFormValues) => void;
  readonly onCancel: () => void;
}

/** Dialog collecting an account and its token; the token stays in this form only. */
export function AccountForm({
  title,
  fields,
  initial,
  busy,
  onSubmit,
  onCancel,
}: AccountFormProps) {
  const { t } = useTranslation();
  const id = useId();
  const [name, setName] = useState(initial.name);
  const [environment, setEnvironment] = useState<Environment>(initial.environment);
  const [readOnly, setReadOnly] = useState(initial.readOnly);
  const [token, setToken] = useState("");
  const [validated, setValidated] = useState(false);
  const nameValid = !fields.name || isValidName(name);
  const tokenValid = isValidToken(token);

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidated(true);
    if (nameValid && tokenValid) {
      onSubmit({ name: name.trim(), environment, readOnly, token });
    }
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered>
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`}>{title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {fields.name && (
            <Form.Group className="mb-3" controlId={`${id}-name`}>
              <Form.Label>{t("field.name")}</Form.Label>
              <Form.Control
                value={name}
                maxLength={40}
                required
                autoFocus
                isInvalid={validated && !nameValid}
                aria-describedby={`${id}-name-help`}
                onChange={(event) => {
                  setName(event.target.value);
                }}
              />
              <Form.Text id={`${id}-name-help`}>{t("field.name.help")}</Form.Text>
              <Form.Control.Feedback type="invalid">{t("validation.name")}</Form.Control.Feedback>
            </Form.Group>
          )}
          {fields.environment && (
            <Form.Group className="mb-3" controlId={`${id}-environment`}>
              <Form.Label>{t("field.environment")}</Form.Label>
              <Form.Select
                value={environment}
                onChange={(event) => {
                  setEnvironment(event.target.value as Environment);
                }}
              >
                <option value="sandbox">{t("environment.sandbox")}</option>
                <option value="production">{t("environment.production")}</option>
              </Form.Select>
            </Form.Group>
          )}
          {fields.readOnly && (
            <Form.Group className="mb-3" controlId={`${id}-read-only`}>
              <Form.Check
                type="checkbox"
                label={t("field.readOnly")}
                checked={readOnly}
                aria-describedby={`${id}-read-only-help`}
                onChange={(event) => {
                  setReadOnly(event.target.checked);
                }}
              />
              <Form.Text id={`${id}-read-only-help`}>{t("field.readOnly.help")}</Form.Text>
            </Form.Group>
          )}
          <Form.Group className="mb-3" controlId={`${id}-token`}>
            <Form.Label>{t("field.token")}</Form.Label>
            <Form.Control
              type="password"
              value={token}
              required
              autoComplete="off"
              spellCheck={false}
              autoFocus={!fields.name}
              isInvalid={validated && !tokenValid}
              aria-describedby={`${id}-token-help`}
              onChange={(event) => {
                setToken(event.target.value.trim());
              }}
            />
            <Form.Text id={`${id}-token-help`}>
              {t("field.token.help")}{" "}
              <a href={ADMIN_URLS[environment]} target="_blank" rel="noopener noreferrer">
                {ADMIN_URLS[environment]}
              </a>
            </Form.Text>
            <Form.Control.Feedback type="invalid">{t("validation.token")}</Form.Control.Feedback>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {t("action.cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={busy}>
            {busy ? t("feedback.saving") : t("action.save")}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
