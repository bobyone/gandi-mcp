// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, useState, type SubmitEvent } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";

/** Longest snapshot name LiveDNS accepts. */
export const MAX_SNAPSHOT_NAME = 255;

export interface SnapshotDialogProps {
  readonly zone: string;
  readonly busy: boolean;
  /** Called with the name typed, empty for a name chosen by Gandi. */
  readonly onSubmit: (name: string) => void;
  readonly onCancel: () => void;
}

/** Dialog creating a snapshot of a zone, with an optional name. */
export function SnapshotDialog({ zone, busy, onSubmit, onCancel }: SnapshotDialogProps) {
  const { t } = useTranslation();
  const id = useId();
  const [name, setName] = useState("");

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(name.trim());
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered>
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`} className="text-break">
            {t("dialog.createSnapshot.title", { zone })}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId={`${id}-name`}>
            <Form.Label>{t("field.snapshotName")}</Form.Label>
            <Form.Control
              value={name}
              autoFocus
              maxLength={MAX_SNAPSHOT_NAME}
              aria-describedby={`${id}-help`}
              onChange={(event) => {
                setName(event.target.value);
              }}
            />
            <Form.Text id={`${id}-help`}>{t("field.snapshotName.help")}</Form.Text>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {t("action.cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={busy}>
            {busy ? t("feedback.saving") : t("action.createSnapshot")}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
