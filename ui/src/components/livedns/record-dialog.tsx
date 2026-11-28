// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, useState, type SubmitEvent } from "react";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import { useTranslation } from "react-i18next";
import {
  isRecordName,
  parseTtl,
  parseValues,
  type DnsRecord,
  type RecordDraft,
} from "../../api/livedns";

export interface RecordDialogProps {
  readonly zone: string;
  /** The record to edit; its name and type are fixed. Absent to add a record. */
  readonly record?: DnsRecord;
  readonly types: readonly string[];
  readonly busy: boolean;
  readonly onSubmit: (record: RecordDraft) => void;
  readonly onCancel: () => void;
}

/** Dialog adding a record, or replacing the values and TTL of one. */
export function RecordDialog({ zone, record, types, busy, onSubmit, onCancel }: RecordDialogProps) {
  const { t } = useTranslation();
  const id = useId();
  const [name, setName] = useState(record?.name ?? "");
  const [type, setType] = useState(record?.type ?? types[0] ?? "A");
  const [ttl, setTtl] = useState(record?.ttl != null ? String(record.ttl) : "");
  const [values, setValues] = useState(record?.values.join("\n") ?? "");
  const [validated, setValidated] = useState(false);
  const parsedValues = parseValues(values);
  const parsedTtl = parseTtl(ttl);
  const validName = isRecordName(name);

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setValidated(true);
    if (!validName || parsedValues === null || parsedTtl === undefined) return;
    onSubmit({ name: name.trim(), type, ttl: parsedTtl, values: parsedValues });
  }

  const title = record
    ? t("dialog.editRecord.title", { name: record.name, type: record.type })
    : t("dialog.addRecord.title", { zone });
  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered size="lg">
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`} className="text-break">
            {title}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId={`${id}-name`} className="mb-3">
            <Form.Label>{t("field.recordName")}</Form.Label>
            <Form.Control
              value={name}
              required
              readOnly={record !== undefined}
              autoFocus={record === undefined}
              spellCheck={false}
              maxLength={255}
              isInvalid={validated && !validName}
              aria-describedby={`${id}-name-help`}
              onChange={(event) => {
                setName(event.target.value);
              }}
            />
            <Form.Text id={`${id}-name-help`}>{t("field.recordName.help")}</Form.Text>
            <Form.Control.Feedback type="invalid">
              {t("validation.recordName")}
            </Form.Control.Feedback>
          </Form.Group>
          <Form.Group controlId={`${id}-type`} className="mb-3">
            <Form.Label>{t("field.recordType")}</Form.Label>
            <Form.Select
              value={type}
              disabled={record !== undefined}
              onChange={(event) => {
                setType(event.target.value);
              }}
            >
              {(types.includes(type) ? types : [type, ...types]).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group controlId={`${id}-ttl`} className="mb-3">
            <Form.Label>{t("field.ttl")}</Form.Label>
            <Form.Control
              value={ttl}
              inputMode="numeric"
              autoFocus={record !== undefined}
              isInvalid={validated && parsedTtl === undefined}
              aria-describedby={`${id}-ttl-help`}
              onChange={(event) => {
                setTtl(event.target.value);
              }}
            />
            <Form.Text id={`${id}-ttl-help`}>{t("field.ttl.help")}</Form.Text>
            <Form.Control.Feedback type="invalid">{t("validation.ttl")}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group controlId={`${id}-values`}>
            <Form.Label>{t("field.recordValues")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={5}
              value={values}
              required
              spellCheck={false}
              className="font-monospace"
              isInvalid={validated && parsedValues === null}
              aria-describedby={`${id}-values-help`}
              onChange={(event) => {
                setValues(event.target.value);
              }}
            />
            <Form.Text id={`${id}-values-help`}>{t("field.recordValues.help")}</Form.Text>
            <Form.Control.Feedback type="invalid">
              {t("validation.recordValues")}
            </Form.Control.Feedback>
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
