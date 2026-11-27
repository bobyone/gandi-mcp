// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useEffect, useId, useState, type SubmitEvent } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";
import { MIN_YEARS, pickYears } from "../../api/domain";
import type { DomainsApi } from "../../api/domains-api";
import { DurationPrice } from "./duration-price";
import { useQuote } from "./use-quote";

export interface RenewDialogProps {
  readonly api: DomainsApi;
  readonly account: string;
  readonly fqdn: string;
  readonly displayName: string;
  readonly busy: boolean;
  readonly onSubmit: (years: number) => void;
  readonly onCancel: () => void;
}

/** Preview of a renewal: duration and indicative price; the server confirms the amount. */
export function RenewDialog(props: RenewDialogProps) {
  const { api, account, fqdn, displayName, busy, onSubmit, onCancel } = props;
  const { t } = useTranslation();
  const id = useId();
  const { state, ask } = useQuote(api, account, "renew");
  const [years, setYears] = useState(MIN_YEARS);
  const chosen = state.kind === "ready" ? pickYears(state.quote, years) : years;

  useEffect(() => {
    void ask(fqdn);
  }, [ask, fqdn]);

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(chosen);
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered>
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`}>
            {t("dialog.renew.title", { name: displayName })}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {state.kind === "ready" ? (
            <DurationPrice quote={state.quote} years={chosen} onChange={setYears} />
          ) : state.kind === "failed" ? (
            <Alert variant="danger">{state.message || t("feedback.failed")}</Alert>
          ) : (
            <div role="status" className="mb-3">
              <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
              {t("price.loading")}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {t("action.cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={busy || state.kind !== "ready"}>
            {t("action.renew")}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
