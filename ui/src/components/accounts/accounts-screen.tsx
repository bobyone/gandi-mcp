// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useEffect, useState } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Dropdown from "react-bootstrap/Dropdown";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";
import { AccountsError, type Account, type AccountChanges } from "../../api/account";
import { isPending } from "../../api/pending-confirmation";
import type { AccountsApi } from "../../api/accounts-api";
import { AccountForm, type AccountFormValues } from "./account-form";
import { ConfirmDialog } from "../confirm-dialog";
import { FeedbackArea, type Feedback } from "../feedback-area";
import { PayingOrganizationForm } from "./paying-organization-form";
import { RenameForm } from "./rename-form";

type Dialog =
  | { kind: "add" }
  | {
      kind:
        | "rename"
        | "replaceToken"
        | "changeEnvironment"
        | "remove"
        | "allowWrites"
        | "payingOrganization";
      account: Account;
    };

/** A change the server asked the user to confirm outside the App. */
type Pending =
  | { kind: "remove"; account: Account; confirmationId: string }
  | { kind: "update"; account: Account; changes: AccountChanges; confirmationId: string };

export interface AccountsScreenProps {
  readonly api: AccountsApi;
}

/** The "Accounts" screen: list the accounts and manage them. */
export function AccountsScreen({ api }: AccountsScreenProps) {
  const { t } = useTranslation();
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);

  const failure = useCallback(
    (error: unknown) => {
      const text = error instanceof AccountsError && error.message ? error.message : "";
      setFeedback({ variant: "danger", text: text || t("feedback.failed") });
    },
    [t],
  );

  const reload = useCallback(async () => {
    try {
      setAccounts(await api.list());
    } catch (error) {
      setAccounts((current) => current ?? []);
      failure(error);
    }
  }, [api, failure]);

  useEffect(() => {
    let active = true;
    api.list().then(
      (listed) => {
        if (active) setAccounts(listed);
      },
      (error: unknown) => {
        if (!active) return;
        setAccounts([]);
        failure(error);
      },
    );
    return () => {
      active = false;
    };
  }, [api, failure]);

  /** Run a change; it returns its success text, or null while a confirmation is pending. */
  async function run(action: () => Promise<string | null>) {
    setBusy(true);
    setFeedback(null);
    setPending(null);
    try {
      const text = await action();
      setDialog(null);
      if (text !== null) setFeedback({ variant: "success", text });
      await reload();
    } catch (error) {
      setDialog(null);
      failure(error);
    } finally {
      setBusy(false);
    }
  }

  function add(values: AccountFormValues) {
    void run(async () => {
      const verified = await api.add(values, values.token);
      return t("feedback.saved", { name: verified.account.name, username: verified.username });
    });
  }

  function token(account: Account, values: AccountFormValues, move: boolean) {
    void run(async () => {
      const verified = move
        ? await api.changeEnvironment(account.name, values.environment, values.token)
        : await api.replaceToken(account.name, values.token);
      return t("feedback.saved", { name: verified.account.name, username: verified.username });
    });
  }

  function update(account: Account, changes: AccountChanges, confirmationId?: string) {
    void run(async () => {
      const updated = await api.update(account.name, changes, confirmationId);
      if (isPending(updated)) {
        setPending({ kind: "update", account, changes, ...updated });
        return null;
      }
      return t("feedback.updated", { name: updated.name });
    });
  }

  function remove(account: Account, confirmationId?: string) {
    void run(async () => {
      const result = await api.remove(account.name, confirmationId);
      if (result !== null) {
        setPending({ kind: "remove", account, ...result });
        return null;
      }
      return t("feedback.removed", { name: account.name });
    });
  }

  function choosePayingOrganization(account: Account, organizationId: string | null) {
    void run(async () => {
      const updated = await api.setPayingOrganization(account.name, organizationId);
      return t("feedback.updated", { name: updated.name });
    });
  }

  function resume(waiting: Pending) {
    if (waiting.kind === "remove") remove(waiting.account, waiting.confirmationId);
    else update(waiting.account, waiting.changes, waiting.confirmationId);
  }

  const cancel = () => {
    setDialog(null);
  };

  return (
    <main className="container-fluid py-3">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h1 className="h4 mb-0">{t("app.title")}</h1>
        <Button
          variant="primary"
          onClick={() => {
            setDialog({ kind: "add" });
          }}
        >
          {t("action.add")}
        </Button>
      </div>
      <FeedbackArea
        pending={pending !== null}
        feedback={feedback}
        busy={busy}
        onContinue={() => {
          if (pending) resume(pending);
        }}
        onDismiss={() => {
          setFeedback(null);
        }}
      />
      {accounts === null ? (
        <div role="status" className="mb-3">
          <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
          {t("accounts.loading")}
        </div>
      ) : accounts.length === 0 ? (
        <p>{t("accounts.empty")}</p>
      ) : (
        <>
          <p className="text-body-secondary">{t("accounts.count", { count: accounts.length })}</p>
          <Table responsive hover className="align-middle">
            <thead>
              <tr>
                <th scope="col">{t("column.name")}</th>
                <th scope="col">{t("column.environment")}</th>
                <th scope="col">{t("column.status")}</th>
                <th scope="col">
                  <span className="visually-hidden">{t("column.actions")}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((account) => (
                <tr key={account.name}>
                  <th scope="row">{account.name}</th>
                  <td>
                    <Badge bg={account.environment === "production" ? "danger" : "info"}>
                      {t(`environment.${account.environment}`)}
                    </Badge>
                  </td>
                  <td className="d-flex flex-wrap gap-1">
                    {account.isDefault && <Badge bg="primary">{t("status.default")}</Badge>}
                    {account.readOnly && <Badge bg="secondary">{t("status.readOnly")}</Badge>}
                    {account.removalPending && (
                      <Badge bg="warning" text="dark">
                        {t("status.removalPending")}
                      </Badge>
                    )}
                  </td>
                  <td className="text-end">
                    <Dropdown align="end">
                      <Dropdown.Toggle
                        variant="outline-secondary"
                        size="sm"
                        aria-label={t("actions.for", { name: account.name })}
                      >
                        {t("column.actions")}
                      </Dropdown.Toggle>
                      <Dropdown.Menu>
                        <Dropdown.Item
                          onClick={() => {
                            setDialog({ kind: "rename", account });
                          }}
                        >
                          {t("action.rename")}
                        </Dropdown.Item>
                        <Dropdown.Item
                          onClick={() => {
                            setDialog({ kind: "replaceToken", account });
                          }}
                        >
                          {t("action.replaceToken")}
                        </Dropdown.Item>
                        <Dropdown.Item
                          onClick={() => {
                            setDialog({ kind: "changeEnvironment", account });
                          }}
                        >
                          {t("action.changeEnvironment")}
                        </Dropdown.Item>
                        <Dropdown.Item
                          onClick={() => {
                            setDialog({ kind: "payingOrganization", account });
                          }}
                        >
                          {t("action.choosePayingOrganization")}
                        </Dropdown.Item>
                        {!account.isDefault && (
                          <Dropdown.Item
                            onClick={() => {
                              update(account, { makeDefault: true });
                            }}
                          >
                            {t("action.setDefault")}
                          </Dropdown.Item>
                        )}
                        {account.readOnly ? (
                          <Dropdown.Item
                            onClick={() => {
                              setDialog({ kind: "allowWrites", account });
                            }}
                          >
                            {t("action.allowWrites")}
                          </Dropdown.Item>
                        ) : (
                          <Dropdown.Item
                            onClick={() => {
                              update(account, { readOnly: true });
                            }}
                          >
                            {t("action.makeReadOnly")}
                          </Dropdown.Item>
                        )}
                        <Dropdown.Divider />
                        <Dropdown.Item
                          className="text-danger"
                          onClick={() => {
                            setDialog({ kind: "remove", account });
                          }}
                        >
                          {t("action.remove")}
                        </Dropdown.Item>
                      </Dropdown.Menu>
                    </Dropdown>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}
      {dialog?.kind === "add" && (
        <AccountForm
          title={t("dialog.add.title")}
          fields={{ name: true, environment: true, readOnly: true }}
          initial={{ name: "", environment: "sandbox", readOnly: false }}
          busy={busy}
          onSubmit={add}
          onCancel={cancel}
        />
      )}
      {(dialog?.kind === "replaceToken" || dialog?.kind === "changeEnvironment") && (
        <AccountForm
          title={t(`dialog.${dialog.kind}.title`, { name: dialog.account.name })}
          fields={{
            name: false,
            environment: dialog.kind === "changeEnvironment",
            readOnly: false,
          }}
          initial={{
            name: dialog.account.name,
            environment:
              dialog.kind === "changeEnvironment"
                ? dialog.account.environment === "production"
                  ? "sandbox"
                  : "production"
                : dialog.account.environment,
            readOnly: dialog.account.readOnly,
          }}
          busy={busy}
          onSubmit={(values) => {
            token(dialog.account, values, dialog.kind === "changeEnvironment");
          }}
          onCancel={cancel}
        />
      )}
      {dialog?.kind === "rename" && (
        <RenameForm
          name={dialog.account.name}
          busy={busy}
          onSubmit={(newName) => {
            update(dialog.account, { newName });
          }}
          onCancel={cancel}
        />
      )}
      {dialog?.kind === "payingOrganization" && (
        <PayingOrganizationForm
          api={api}
          account={dialog.account}
          busy={busy}
          onSubmit={(organizationId) => {
            choosePayingOrganization(dialog.account, organizationId);
          }}
          onCancel={cancel}
        />
      )}
      {dialog?.kind === "remove" && (
        <ConfirmDialog
          title={t("dialog.remove.title", { name: dialog.account.name })}
          body={t("dialog.remove.body")}
          confirmLabel={t("action.remove")}
          variant="danger"
          busy={busy}
          onConfirm={() => {
            remove(dialog.account);
          }}
          onCancel={cancel}
        />
      )}
      {dialog?.kind === "allowWrites" && (
        <ConfirmDialog
          title={t("dialog.allowWrites.title", { name: dialog.account.name })}
          body={t("dialog.allowWrites.body")}
          confirmLabel={t("action.allowWrites")}
          variant="warning"
          busy={busy}
          onConfirm={() => {
            update(dialog.account, { readOnly: false });
          }}
          onCancel={cancel}
        />
      )}
    </main>
  );
}
