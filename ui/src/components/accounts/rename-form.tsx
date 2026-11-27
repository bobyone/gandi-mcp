// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, useState, type SubmitEvent } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";
import { isValidName } from "../../api/account";

export interface RenameFormProps {
  readonly name: string;
  readonly busy: boolean;
  readonly onSubmit: (newName: string) => void;
  readonly onCancel: () => void;
}

/** Dialog renaming an account. */
export function RenameForm({ name, busy, onSubmit, onCancel }: RenameFormProps) {
  const { t } = useTranslation();
  const id = useId();
  const [value, setValue] = useState(name);
  const [validated, setValidated] = useState(false);
  const valid = isValidName(value);

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidated(true);
    if (valid) onSubmit(value.trim());
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered>
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`}>{t("dialog.rename.title", { name })}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId={`${id}-name`}>
            <Form.Label>{t("field.name")}</Form.Label>
            <Form.Control
              value={value}
              maxLength={40}
              required
              autoFocus
              isInvalid={validated && !valid}
              aria-describedby={`${id}-help`}
              onChange={(event) => {
                setValue(event.target.value);
              }}
            />
            <Form.Text id={`${id}-help`}>{t("field.name.help")}</Form.Text>
            <Form.Control.Feedback type="invalid">{t("validation.name")}</Form.Control.Feedback>
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
