// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useEffect, useId, useState, type SubmitEvent } from "react";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";
import Modal from "react-bootstrap/Modal";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";
import { AccountsError, type Account } from "../../api/account";
import type { AccountsApi } from "../../api/accounts-api";
import type { Organization } from "../../api/organization";

export interface PayingOrganizationFormProps {
  readonly api: AccountsApi;
  readonly account: Account;
  readonly busy: boolean;
  /** The chosen organization identifier, or null to clear the choice. */
  readonly onSubmit: (organizationId: string | null) => void;
  readonly onCancel: () => void;
}

/** Dialog choosing the paying organization of an account among its organizations. */
export function PayingOrganizationForm(props: PayingOrganizationFormProps) {
  const { api, account, busy, onSubmit, onCancel } = props;
  const { t } = useTranslation();
  const id = useId();
  const [organizations, setOrganizations] = useState<Organization[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [value, setValue] = useState(account.payingOrganization ?? "");

  useEffect(() => {
    let active = true;
    api.organizations(account.name).then(
      (found) => {
        if (active) setOrganizations(found);
      },
      (failure: unknown) => {
        if (!active) return;
        setOrganizations([]);
        setError(
          failure instanceof AccountsError && failure.message
            ? failure.message
            : t("feedback.failed"),
        );
      },
    );
    return () => {
      active = false;
    };
  }, [api, account.name, t]);

  function submit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit(value === "" ? null : value);
  }

  return (
    <Modal show onHide={onCancel} aria-labelledby={`${id}-title`} centered>
      <Form noValidate onSubmit={submit}>
        <Modal.Header closeButton closeLabel={t("action.close")}>
          <Modal.Title id={`${id}-title`}>
            {t("dialog.payingOrganization.title", { name: account.name })}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          {organizations === null ? (
            <div role="status" className="mb-3">
              <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
              {t("organizations.loading")}
            </div>
          ) : (
            <Form.Group controlId={`${id}-organization`}>
              <Form.Label>{t("field.payingOrganization")}</Form.Label>
              <Form.Select
                value={value}
                onChange={(event) => {
                  setValue(event.target.value);
                }}
              >
                <option value="">{t("field.payingOrganization.none")}</option>
                {organizations.map((organization) => (
                  <option key={organization.id} value={organization.id}>
                    {organization.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={onCancel} disabled={busy}>
            {t("action.cancel")}
          </Button>
          <Button type="submit" variant="primary" disabled={busy || organizations === null}>
            {busy ? t("feedback.saving") : t("action.save")}
          </Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
