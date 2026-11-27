// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useEffect, useId, useState, type SubmitEvent } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import InputGroup from "react-bootstrap/InputGroup";
import Pagination from "react-bootstrap/Pagination";
import Row from "react-bootstrap/Row";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";
import type { Account } from "../../api/account";
import type { AccountsApi } from "../../api/accounts-api";
import { DomainsError, type DomainPage, type DomainSummary } from "../../api/domain";
import type { DomainsApi } from "../../api/domains-api";
import type { PendingConfirmation } from "../../api/pending-confirmation";
import { FeedbackArea, type Feedback } from "../feedback-area";
import { DomainDetailsDialog, type DetailsState } from "./domain-details";
import { formatDate } from "./format";
import { NameserversForm } from "./nameservers-form";
import { RegisterDialog } from "./register-dialog";
import { RenewDialog } from "./renew-dialog";

export const PER_PAGE = 25;

/** A change sent to the server; called again with the confirmation identifier. */
type Change = (confirmationId?: string) => Promise<PendingConfirmation | null>;

interface Pending {
  readonly change: Change;
  readonly success: string;
  readonly confirmationId: string;
}

type Dialog = "nameservers" | "renew" | "register";

export interface DomainsScreenProps {
  readonly domains: DomainsApi;
  readonly accounts: AccountsApi;
}

function message(error: unknown): string {
  return (error instanceof DomainsError || error instanceof Error) && error.message
    ? error.message
    : "";
}

/** The "Domains" screen: the domains of an account, their details and common actions. */
export function DomainsScreen({ domains, accounts }: DomainsScreenProps) {
  const { t, i18n } = useTranslation();
  const id = useId();
  const [accountList, setAccountList] = useState<Account[] | null>(null);
  const [account, setAccount] = useState<string>("");
  const [filterText, setFilterText] = useState("");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{ key: string; listing: DomainPage | null } | null>(null);
  const [selected, setSelected] = useState<DomainSummary | null>(null);
  const [details, setDetails] = useState<DetailsState>({ kind: "loading" });
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);

  const failed = useCallback(
    (error: unknown) => {
      setFeedback({ variant: "danger", text: message(error) || t("feedback.failed") });
    },
    [t],
  );

  useEffect(() => {
    let active = true;
    accounts.list().then(
      (found) => {
        if (!active) return;
        setAccountList(found);
        setAccount((found.find((item) => item.isDefault) ?? found[0])?.name ?? "");
      },
      (error: unknown) => {
        if (!active) return;
        setAccountList([]);
        failed(error);
      },
    );
    return () => {
      active = false;
    };
  }, [accounts, failed]);

  /** The page asked for; `version` changes to read it again after a change. */
  const key = JSON.stringify([account, page, filter, version]);
  useEffect(() => {
    if (account === "") return;
    let active = true;
    domains.list(account, page, PER_PAGE, filter).then(
      (found) => {
        if (active) setResult({ key, listing: found });
      },
      (error: unknown) => {
        if (!active) return;
        setResult({ key, listing: null });
        failed(error);
      },
    );
    return () => {
      active = false;
    };
  }, [domains, account, page, filter, key, failed]);
  const loading = account !== "" && result?.key !== key;
  const listing = result?.listing ?? null;

  const loadDetails = useCallback(
    async (fqdn: string) => {
      setDetails({ kind: "loading" });
      try {
        setDetails({ kind: "ready", details: await domains.details(account, fqdn) });
      } catch (error) {
        setDetails({ kind: "failed", message: message(error) });
      }
    },
    [domains, account],
  );

  function open(domain: DomainSummary) {
    setSelected(domain);
    void loadDetails(domain.fqdn);
  }

  /** Send a change; a pending confirmation is resumed with Continue. */
  async function run(change: Change, success: string, confirmationId?: string) {
    setBusy(true);
    setFeedback(null);
    setPending(null);
    try {
      const outcome = await change(confirmationId);
      setDialog(null);
      if (outcome !== null) {
        setPending({ change, success, confirmationId: outcome.confirmationId });
        return;
      }
      setFeedback({ variant: "success", text: success });
      setVersion((value) => value + 1);
      if (selected) await loadDetails(selected.fqdn);
    } catch (error) {
      setDialog(null);
      failed(error);
    } finally {
      setBusy(false);
    }
  }

  function search(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setFilter(filterText.trim());
  }

  const current = accountList?.find((item) => item.name === account) ?? null;
  const readOnly = current?.readOnly === true;
  const total = listing?.total ?? null;
  const pages = total !== null ? Math.max(1, Math.ceil(total / PER_PAGE)) : null;
  const hasNext =
    listing !== null &&
    (pages !== null ? page < pages : listing.domains.length === listing.perPage);
  const updated = (name: string) => t("feedback.domainUpdated", { name });

  return (
    <main className="container-fluid py-3">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h1 className="h4 mb-0">{t("domains.title")}</h1>
        {current && !readOnly && (
          <Button
            variant="primary"
            onClick={() => {
              setDialog("register");
            }}
          >
            {t("action.register")}
          </Button>
        )}
      </div>
      <FeedbackArea
        pending={pending !== null}
        feedback={feedback}
        busy={busy}
        onContinue={() => {
          if (pending) void run(pending.change, pending.success, pending.confirmationId);
        }}
        onDismiss={() => {
          setFeedback(null);
        }}
      />
      {accountList === null ? (
        <div role="status" className="mb-3">
          <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
          {t("accounts.loading")}
        </div>
      ) : accountList.length === 0 ? (
        <p>{t("domains.noAccount")}</p>
      ) : (
        <>
          <Form onSubmit={search} className="mb-3">
            <Row className="g-2 align-items-end">
              <Col xs={12} md={4}>
                <Form.Group controlId={`${id}-account`}>
                  <Form.Label>{t("field.account")}</Form.Label>
                  <Form.Select
                    value={account}
                    onChange={(event) => {
                      setAccount(event.target.value);
                      setPage(1);
                      setSelected(null);
                    }}
                  >
                    {accountList.map((item) => (
                      <option key={item.name} value={item.name}>
                        {item.name}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col xs={12} md={8}>
                <Form.Group controlId={`${id}-filter`}>
                  <Form.Label>{t("field.domainFilter")}</Form.Label>
                  <InputGroup>
                    <Form.Control
                      value={filterText}
                      maxLength={253}
                      spellCheck={false}
                      aria-describedby={`${id}-filter-help`}
                      onChange={(event) => {
                        setFilterText(event.target.value);
                      }}
                    />
                    <Button type="submit" variant="outline-primary">
                      {t("action.search")}
                    </Button>
                  </InputGroup>
                  <Form.Text id={`${id}-filter-help`}>{t("field.domainFilter.help")}</Form.Text>
                </Form.Group>
              </Col>
            </Row>
          </Form>
          {readOnly && (
            <p>
              <Badge bg="secondary">{t("status.readOnly")}</Badge>
            </p>
          )}
          {loading || listing === null ? (
            loading && (
              <div role="status" className="mb-3">
                <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
                {t("domains.loading")}
              </div>
            )
          ) : listing.domains.length === 0 ? (
            <p>{t("domains.empty")}</p>
          ) : (
            <>
              {total !== null && (
                <p className="text-body-secondary">{t("domains.count", { count: total })}</p>
              )}
              <Table responsive hover className="align-middle">
                <thead>
                  <tr>
                    <th scope="col">{t("column.domain")}</th>
                    <th scope="col">{t("column.expiry")}</th>
                    <th scope="col">{t("column.autorenew")}</th>
                    <th scope="col">{t("column.transferLock")}</th>
                    <th scope="col">{t("column.status")}</th>
                    <th scope="col">
                      <span className="visually-hidden">{t("column.actions")}</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {listing.domains.map((domain) => (
                    <tr key={domain.fqdn}>
                      <th scope="row" className="text-break">
                        {domain.displayName}
                      </th>
                      <td>{formatDate(domain.expiresAt, i18n.language) ?? t("details.none")}</td>
                      <td>{domain.autorenew === true ? t("value.on") : t("value.off")}</td>
                      <td>{domain.transferLock ? t("value.on") : t("value.off")}</td>
                      <td className="d-flex flex-wrap gap-1">
                        {domain.statuses.map((status) => (
                          <Badge key={status} bg="secondary">
                            {status}
                          </Badge>
                        ))}
                      </td>
                      <td className="text-end">
                        <Button
                          variant="outline-secondary"
                          size="sm"
                          aria-label={t("action.detailsFor", { name: domain.displayName })}
                          onClick={() => {
                            open(domain);
                          }}
                        >
                          {t("action.details")}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
              <nav aria-label={t("pagination.label")}>
                <Pagination className="flex-wrap align-items-center">
                  <Pagination.Prev
                    disabled={page <= 1}
                    aria-label={t("pagination.previous")}
                    onClick={() => {
                      setPage(page - 1);
                    }}
                  />
                  <li className="px-3" aria-current="page">
                    {pages !== null
                      ? t("pagination.pageOf", { page, pages })
                      : t("pagination.page", { page })}
                  </li>
                  <Pagination.Next
                    disabled={!hasNext}
                    aria-label={t("pagination.next")}
                    onClick={() => {
                      setPage(page + 1);
                    }}
                  />
                </Pagination>
              </nav>
            </>
          )}
        </>
      )}
      {selected && dialog === null && (
        <DomainDetailsDialog
          state={details}
          readOnly={readOnly}
          busy={busy}
          onAutorenew={(enabled) => {
            void run(
              () => domains.setAutorenew(account, selected.fqdn, enabled),
              updated(selected.displayName),
            );
          }}
          onTransferLock={(locked) => {
            void run(
              (confirmationId) =>
                domains.setTransferLock(account, selected.fqdn, locked, confirmationId),
              updated(selected.displayName),
            );
          }}
          onEditNameservers={() => {
            setDialog("nameservers");
          }}
          onRenew={() => {
            setDialog("renew");
          }}
          onClose={() => {
            setSelected(null);
          }}
        />
      )}
      {selected && dialog === "nameservers" && (
        <NameserversForm
          domain={selected.displayName}
          nameservers={details.kind === "ready" ? details.details.nameservers : []}
          busy={busy}
          onSubmit={(nameservers) => {
            void run(
              (confirmationId) =>
                domains.setNameservers(account, selected.fqdn, nameservers, confirmationId),
              updated(selected.displayName),
            );
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
      {selected && dialog === "renew" && (
        <RenewDialog
          api={domains}
          account={account}
          fqdn={selected.fqdn}
          displayName={selected.displayName}
          busy={busy}
          onSubmit={(years) => {
            void run(
              (confirmationId) => domains.renew(account, selected.fqdn, years, confirmationId),
              t("feedback.ordered", { name: selected.displayName }),
            );
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
      {dialog === "register" && (
        <RegisterDialog
          api={domains}
          account={account}
          busy={busy}
          onSubmit={(fqdn, years, owner) => {
            void run(
              (confirmationId) => domains.register(account, fqdn, years, owner, confirmationId),
              t("feedback.ordered", { name: fqdn }),
            );
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
    </main>
  );
}
