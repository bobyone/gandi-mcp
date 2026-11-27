// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, useState, type SubmitEvent } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";
import {
  EMPTY_CONTACT,
  MIN_YEARS,
  invalidContactFields,
  isAvailable,
  looksLikeDomain,
  pickYears,
  type ContactDraft,
} from "../../api/domain";
import type { DomainsApi } from "../../api/domains-api";
import { ContactForm } from "./contact-form";
import { DurationPrice } from "./duration-price";
import { useQuote } from "./use-quote";

export interface RegisterDialogProps {
  readonly api: DomainsApi;
  readonly account: string;
  readonly busy: boolean;
  readonly onSubmit: (fqdn: string, years: number, owner: ContactDraft) => void;
  readonly onCancel: () => void;
}

/**
 * Preview of a registration: availability, duration, indicative price and owner. The
 * server then shows the exact amount in its confirmation.
 */
export function RegisterDialog({ api, account, busy, onSubmit, onCancel }: RegisterDialogProps) {
  const { t } = useTranslation();
  const id = useId();
  const { state, ask, reset } = useQuote(api, account, "create");
  const [name, setName] = useState("");
  const [checked, setChecked] = useState("");
  const [nameValidated, setNameValidated] = useState(false);
  const [years, setYears] = useState(MIN_YEARS);
  const [owner, setOwner] = useState<ContactDraft>(EMPTY_CONTACT);
  const [validated, setValidated] = useState(false);
  const invalid = invalidContactFields(owner);
  const available = state.kind === "ready" && isAvailable(state.quote);
  const chosen = state.kind === "ready" ? pickYears(state.quote, years) : years;

  function check() {
    setNameValidated(true);
    if (!looksLikeDomain(name)) return;
    const fqdn = name.trim();
    setChecked(fqdn);
    void ask(fqdn);
  }

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!available) return;
    setValidated(true);
    if (invalid.size === 0) onSubmit(checked, chosen, owner);
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered size="lg">
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`}>{t("dialog.register.title")}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group controlId={`${id}-domain`} className="mb-3">
            <Form.Label>{t("field.domain")}</Form.Label>
            <InputGroup hasValidation>
              <Form.Control
                value={name}
                maxLength={253}
                required
                autoFocus
                spellCheck={false}
                isInvalid={nameValidated && !looksLikeDomain(name)}
                onChange={(event) => {
                  setName(event.target.value);
                  reset();
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !available) {
                    event.preventDefault();
                    check();
                  }
                }}
              />
              <Button variant="outline-primary" onClick={check} disabled={state.kind === "loading"}>
                {t("action.checkAvailability")}
              </Button>
              <Form.Control.Feedback type="invalid">{t("validation.domain")}</Form.Control.Feedback>
            </InputGroup>
          </Form.Group>
          <div aria-live="polite">
            {state.kind === "loading" && (
              <div role="status" className="mb-3">
                <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
                {t("price.loading")}
              </div>
            )}
            {state.kind === "failed" && (
              <Alert variant="danger">{state.message || t("feedback.failed")}</Alert>
            )}
            {state.kind === "ready" &&
              (available ? (
                <Alert variant="success">{t("availability.available", { name: checked })}</Alert>
              ) : (
                <Alert variant="warning">{t("availability.unavailable", { name: checked })}</Alert>
              ))}
          </div>
          {state.kind === "ready" && available && (
            <>
              <DurationPrice quote={state.quote} years={chosen} onChange={setYears} />
              <ContactForm
                contact={owner}
                invalid={invalid}
                validated={validated}
                onChange={setOwner}
              />
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {t("action.cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={busy || !available}>
            {t("action.register")}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
