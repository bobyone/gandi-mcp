// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useEffect, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Dropdown from "react-bootstrap/Dropdown";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";
import { AccountsError, type Account } from "../api/account";
import type { AccountsApi } from "../api/accounts-api";
import { AccountForm, type AccountFormValues } from "./account-form";
import { ConfirmDialog } from "./confirm-dialog";
import { RenameForm } from "./rename-form";

type Dialog =
  | { kind: "add" }
  | {
      kind: "rename" | "replaceToken" | "changeEnvironment" | "remove" | "allowWrites";
      account: Account;
    };

type Feedback = { variant: "success"; text: string } | { variant: "danger"; text: string };

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

  async function run(action: () => Promise<string>) {
    setBusy(true);
    setFeedback(null);
    try {
      const text = await action();
      setDialog(null);
      setFeedback({ variant: "success", text });
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

  function update(account: Account, changes: Parameters<AccountsApi["update"]>[1]) {
    void run(async () => {
      const updated = await api.update(account.name, changes);
      return t("feedback.updated", { name: updated.name });
    });
  }

  function remove(account: Account) {
    void run(async () => {
      await api.remove(account.name);
      return t("feedback.removed", { name: account.name });
    });
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
      <div aria-live="polite">
        {feedback && (
          <Alert
            variant={feedback.variant}
            dismissible
            closeLabel={t("action.close")}
            onClose={() => {
              setFeedback(null);
            }}
          >
            {feedback.text}
          </Alert>
        )}
      </div>
      {accounts === null ? (
        <p role="status">
          <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
          {t("accounts.loading")}
        </p>
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
