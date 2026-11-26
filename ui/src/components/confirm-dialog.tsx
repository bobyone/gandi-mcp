// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId } from "react";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";

export interface ConfirmDialogProps {
  readonly title: string;
  readonly body: string;
  readonly confirmLabel: string;
  readonly variant: "danger" | "warning";
  readonly busy: boolean;
  readonly onConfirm: () => void;
  readonly onCancel: () => void;
}

/** Ask the user to confirm an action; this click is the user's confirmation. */
export function ConfirmDialog(props: ConfirmDialogProps) {
  const { t } = useTranslation();
  const id = useId();
  return (
    <Modal show onHide={props.onCancel} aria-labelledby={`${id}-title`} centered>
      <Modal.Header closeButton closeLabel={t("action.close")}>
        <Modal.Title id={`${id}-title`}>{props.title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>{props.body}</Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={props.onCancel} disabled={props.busy} autoFocus>
          {t("action.cancel")}
        </Button>
        <Button variant={props.variant} onClick={props.onConfirm} disabled={props.busy}>
          {props.confirmLabel}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
