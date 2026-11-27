// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId, type ReactNode } from "react";
import Alert from "react-bootstrap/Alert";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Card from "react-bootstrap/Card";
import Col from "react-bootstrap/Col";
import Modal from "react-bootstrap/Modal";
import Row from "react-bootstrap/Row";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";
import type { ContactRole, DomainDetails } from "../../api/domain";
import { formatDate } from "./format";

export type DetailsState =
  | { kind: "loading" }
  | { kind: "ready"; details: DomainDetails }
  | { kind: "failed"; message: string };

export interface DomainDetailsDialogProps {
  readonly state: DetailsState;
  /** Writes are refused on a read-only account: no action is offered. */
  readonly readOnly: boolean;
  readonly busy: boolean;
  /** The screen's feedback, shown inside the dialog so that it stays reachable. */
  readonly notice?: ReactNode;
  readonly onAutorenew: (enabled: boolean) => void;
  readonly onTransferLock: (locked: boolean) => void;
  readonly onEditNameservers: () => void;
  readonly onRenew: () => void;
  readonly onClose: () => void;
}

/** Details of a domain, with its contacts in full, and its common actions. */
export function DomainDetailsDialog(props: DomainDetailsDialogProps) {
  const { state, readOnly, busy, notice, onClose } = props;
  const { t } = useTranslation();
  const id = useId();
  const title =
    state.kind === "ready"
      ? t("details.title", { name: state.details.displayName })
      : t("details.loading");
  return (
    <Modal show onHide={onClose} aria-labelledby={`${id}-title`} centered size="lg" scrollable>
      <Modal.Header closeButton closeLabel={t("action.close")}>
        <Modal.Title id={`${id}-title`}>{title}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        {notice}
        {state.kind === "loading" && (
          <div role="status" className="mb-3">
            <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
            {t("details.loading")}
          </div>
        )}
        {state.kind === "failed" && (
          <Alert variant="danger">{state.message || t("feedback.failed")}</Alert>
        )}
        {state.kind === "ready" && <DetailsBody details={state.details} />}
      </Modal.Body>
      <Modal.Footer className="justify-content-between">
        {state.kind === "ready" && !readOnly ? (
          <div className="d-flex flex-wrap gap-2">
            <Button
              variant="outline-primary"
              disabled={busy}
              onClick={() => {
                props.onAutorenew(state.details.autorenew !== true);
              }}
            >
              {state.details.autorenew === true
                ? t("action.disableAutorenew")
                : t("action.enableAutorenew")}
            </Button>
            <Button
              variant="outline-primary"
              disabled={busy}
              onClick={() => {
                props.onTransferLock(!state.details.transferLock);
              }}
            >
              {state.details.transferLock ? t("action.unlockTransfer") : t("action.lockTransfer")}
            </Button>
            <Button variant="outline-primary" disabled={busy} onClick={props.onEditNameservers}>
              {t("action.editNameservers")}
            </Button>
            <Button variant="primary" disabled={busy} onClick={props.onRenew}>
              {t("action.renew")}
            </Button>
          </div>
        ) : (
          <span />
        )}
        <Button variant="secondary" onClick={onClose}>
          {t("action.close")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
}

function DetailsBody({ details }: { readonly details: DomainDetails }) {
  const { t, i18n } = useTranslation();
  const none = t("details.none");
  const roleLabel = (role: ContactRole): string =>
    role === "owner"
      ? t("role.owner")
      : role === "admin"
        ? t("role.admin")
        : role === "tech"
          ? t("role.tech")
          : t("role.bill");
  return (
    <>
      <dl className="row mb-3">
        <dt className="col-sm-4">{t("details.created")}</dt>
        <dd className="col-sm-8">{formatDate(details.createdAt, i18n.language) ?? none}</dd>
        <dt className="col-sm-4">{t("column.expiry")}</dt>
        <dd className="col-sm-8">{formatDate(details.expiresAt, i18n.language) ?? none}</dd>
        <dt className="col-sm-4">{t("column.autorenew")}</dt>
        <dd className="col-sm-8">{details.autorenew === true ? t("value.on") : t("value.off")}</dd>
        <dt className="col-sm-4">{t("column.transferLock")}</dt>
        <dd className="col-sm-8">{details.transferLock ? t("value.on") : t("value.off")}</dd>
        <dt className="col-sm-4">{t("column.status")}</dt>
        <dd className="col-sm-8 d-flex flex-wrap gap-1">
          {details.statuses.length === 0
            ? none
            : details.statuses.map((status) => (
                <Badge key={status} bg="secondary">
                  {status}
                </Badge>
              ))}
        </dd>
        <dt className="col-sm-4">{t("field.nameservers")}</dt>
        <dd className="col-sm-8">
          {details.nameservers.length === 0 ? (
            none
          ) : (
            <ul className="list-unstyled mb-0">
              {details.nameservers.map((nameserver) => (
                <li key={nameserver}>{nameserver}</li>
              ))}
            </ul>
          )}
        </dd>
        <dt className="col-sm-4">{t("details.tags")}</dt>
        <dd className="col-sm-8 d-flex flex-wrap gap-1">
          {details.tags.length === 0
            ? none
            : details.tags.map((tag) => (
                <Badge key={tag} bg="info">
                  {tag}
                </Badge>
              ))}
        </dd>
      </dl>
      <h3 className="h6">{t("details.contacts")}</h3>
      {details.contacts.length === 0 ? (
        <p>{none}</p>
      ) : (
        <Row xs={1} md={2} className="g-2">
          {details.contacts.map((contact) => (
            <Col key={contact.role}>
              <Card className="h-100">
                <Card.Body>
                  <Card.Title as="h4" className="h6">
                    {roleLabel(contact.role)}
                  </Card.Title>
                  <dl className="mb-0 small">
                    {contact.fields.map(({ field, value }) => (
                      <div key={field}>
                        <dt className="d-inline me-1">{t(`contact.${field}`)}</dt>
                        <dd className="d-inline text-break">{value}</dd>
                      </div>
                    ))}
                  </dl>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </>
  );
}
