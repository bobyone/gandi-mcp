// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useEffect, useId, useState } from "react";
import Badge from "react-bootstrap/Badge";
import Button from "react-bootstrap/Button";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import Pagination from "react-bootstrap/Pagination";
import Row from "react-bootstrap/Row";
import Spinner from "react-bootstrap/Spinner";
import { useTranslation } from "react-i18next";
import type { Account } from "../../api/account";
import type { AccountsApi } from "../../api/accounts-api";
import {
  LiveDnsError,
  type DnsRecord,
  type RecordDraft,
  type RecordPage,
  type Snapshot,
} from "../../api/livedns";
import type { LiveDnsApi } from "../../api/livedns-api";
import type { PendingConfirmation } from "../../api/pending-confirmation";
import { ConfirmDialog } from "../confirm-dialog";
import { FeedbackArea, type Feedback } from "../feedback-area";
import { RecordDialog } from "./record-dialog";
import { RecordTable } from "./record-table";
import { SnapshotDialog } from "./snapshot-dialog";
import { SnapshotsPanel } from "./snapshots-panel";

export const PER_PAGE = 25;
/** Offered when LiveDNS does not list its record types. */
export const DEFAULT_TYPES = ["A", "AAAA", "CAA", "CNAME", "MX", "NS", "SRV", "TXT"];

/** A change sent to the server; called again with the confirmation identifier. */
type Change = (confirmationId?: string) => Promise<PendingConfirmation | null>;

interface Pending {
  readonly change: Change;
  readonly success: string;
  readonly confirmationId: string;
}

type Dialog =
  | { readonly kind: "add" }
  | { readonly kind: "edit"; readonly record: DnsRecord }
  | { readonly kind: "delete"; readonly record: DnsRecord }
  | { readonly kind: "snapshot" }
  | { readonly kind: "restore"; readonly snapshot: Snapshot };

export interface ZoneScreenProps {
  readonly livedns: LiveDnsApi;
  readonly accounts: AccountsApi;
}

function message(error: unknown): string {
  return (error instanceof LiveDnsError || error instanceof Error) && error.message
    ? error.message
    : "";
}

/** The "DNS zone" screen: the records and snapshots of a LiveDNS domain. */
export function ZoneScreen({ livedns, accounts }: ZoneScreenProps) {
  const { t } = useTranslation();
  const id = useId();
  const [accountList, setAccountList] = useState<Account[] | null>(null);
  const [account, setAccount] = useState("");
  const [zones, setZones] = useState<{ account: string; names: string[] | null } | null>(null);
  const [zone, setZone] = useState("");
  const [types, setTypes] = useState<string[]>(DEFAULT_TYPES);
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<{ key: string; listing: RecordPage | null } | null>(null);
  const [snapshots, setSnapshots] = useState<{ key: string; list: Snapshot[] | null } | null>(null);
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

  useEffect(() => {
    if (account === "") return;
    let active = true;
    livedns.domains(account).then(
      (names) => {
        if (!active) return;
        setZones({ account, names });
        setZone(names[0] ?? "");
      },
      (error: unknown) => {
        if (!active) return;
        setZones({ account, names: null });
        setZone("");
        failed(error);
      },
    );
    livedns.recordTypes(account).then(
      (found) => {
        if (active && found.length > 0) setTypes(found);
      },
      () => {
        // The usual types stay offered; Gandi judges the record anyway.
      },
    );
    return () => {
      active = false;
    };
  }, [livedns, account, failed]);

  /** The page asked for; `version` changes to read it again after a change. */
  const key = JSON.stringify([account, zone, page, typeFilter, version]);
  useEffect(() => {
    if (account === "" || zone === "") return;
    let active = true;
    livedns.records(account, zone, page, PER_PAGE, typeFilter).then(
      (found) => {
        if (!active) return;
        setResult({ key, listing: found });
        // A page beyond the last one (its last record deleted) goes back to the last one.
        const last = found.total !== null ? Math.max(1, Math.ceil(found.total / PER_PAGE)) : null;
        if (found.records.length === 0 && last !== null && page > last) setPage(last);
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
  }, [livedns, account, zone, page, typeFilter, key, failed]);

  const snapshotsKey = JSON.stringify([account, zone, version]);
  useEffect(() => {
    if (account === "" || zone === "") return;
    let active = true;
    livedns.snapshots(account, zone).then(
      (list) => {
        if (active) setSnapshots({ key: snapshotsKey, list });
      },
      (error: unknown) => {
        if (!active) return;
        setSnapshots({ key: snapshotsKey, list: null });
        failed(error);
      },
    );
    return () => {
      active = false;
    };
  }, [livedns, account, zone, snapshotsKey, failed]);

  const zonesReady = zones?.account === account;
  const zoneNames = zonesReady ? zones.names : null;
  const loading = zone !== "" && result?.key !== key;
  const listing = result?.listing ?? null;

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
    } catch (error) {
      setDialog(null);
      failed(error);
    } finally {
      setBusy(false);
    }
  }

  async function create(draft: RecordDraft) {
    setBusy(true);
    setFeedback(null);
    setPending(null);
    const label = { name: draft.name, type: draft.type };
    try {
      const outcome = await livedns.createRecord(account, zone, draft);
      setDialog(null);
      setFeedback({
        variant: "success",
        text:
          outcome === "unchanged"
            ? t("feedback.recordUnchanged", label)
            : t("feedback.recordCreated", label),
      });
      setVersion((value) => value + 1);
    } catch (error) {
      setDialog(null);
      failed(error);
    } finally {
      setBusy(false);
    }
  }

  async function takeSnapshot(name: string) {
    setBusy(true);
    setFeedback(null);
    setPending(null);
    try {
      await livedns.createSnapshot(account, zone, name);
      setDialog(null);
      setFeedback({ variant: "success", text: t("feedback.snapshotCreated") });
      setVersion((value) => value + 1);
    } catch (error) {
      setDialog(null);
      failed(error);
    } finally {
      setBusy(false);
    }
  }

  function chooseAccount(name: string) {
    setAccount(name);
    setZones(null);
    setZone("");
    setTypes(DEFAULT_TYPES);
    setPage(1);
    setPending(null);
  }

  const current = accountList?.find((item) => item.name === account) ?? null;
  const readOnly = current?.readOnly === true;
  const total = listing?.total ?? null;
  const pages = total !== null ? Math.max(1, Math.ceil(total / PER_PAGE)) : null;
  const hasNext =
    listing !== null &&
    (pages !== null ? page < pages : listing.records.length === listing.perPage);

  return (
    <main className="container-fluid py-3">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-3">
        <h1 className="h4 mb-0">{t("zone.title")}</h1>
        {zone !== "" && !readOnly && (
          <Button
            variant="primary"
            disabled={busy}
            onClick={() => {
              setDialog({ kind: "add" });
            }}
          >
            {t("action.addRecord")}
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
          <Row className="g-2 align-items-end mb-3">
            <Col xs={12} md={4}>
              <Form.Group controlId={`${id}-account`}>
                <Form.Label>{t("field.account")}</Form.Label>
                <Form.Select
                  value={account}
                  onChange={(event) => {
                    chooseAccount(event.target.value);
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
            {zoneNames !== null && zoneNames.length > 0 && (
              <>
                <Col xs={12} md={5}>
                  <Form.Group controlId={`${id}-zone`}>
                    <Form.Label>{t("field.liveDnsDomain")}</Form.Label>
                    <Form.Select
                      value={zone}
                      onChange={(event) => {
                        setZone(event.target.value);
                        setPage(1);
                        setPending(null);
                      }}
                    >
                      {zoneNames.map((name) => (
                        <option key={name} value={name}>
                          {name}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>
                <Col xs={12} md={3}>
                  <Form.Group controlId={`${id}-type`}>
                    <Form.Label>{t("field.recordType")}</Form.Label>
                    <Form.Select
                      value={typeFilter}
                      onChange={(event) => {
                        setTypeFilter(event.target.value);
                        setPage(1);
                      }}
                    >
                      <option value="">{t("zone.allTypes")}</option>
                      {types.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </Form.Select>
                  </Form.Group>
                </Col>
              </>
            )}
          </Row>
          {readOnly && (
            <p>
              <Badge bg="secondary">{t("status.readOnly")}</Badge>
            </p>
          )}
          {!zonesReady ? (
            <div role="status" className="mb-3">
              <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
              {t("domains.loading")}
            </div>
          ) : zoneNames === null ? null : zoneNames.length === 0 ? (
            <p>{t("zone.noZone")}</p>
          ) : (
            <>
              {loading ? (
                <div role="status" className="mb-3">
                  <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
                  {t("zone.loading")}
                </div>
              ) : listing === null ? null : (
                <>
                  {listing.records.length === 0 && <p>{t("zone.empty")}</p>}
                  {listing.records.length > 0 && (
                    <>
                      {total !== null && (
                        <p className="text-body-secondary">{t("zone.count", { count: total })}</p>
                      )}
                      <RecordTable
                        records={listing.records}
                        readOnly={readOnly}
                        busy={busy}
                        onEdit={(record) => {
                          setDialog({ kind: "edit", record });
                        }}
                        onDelete={(record) => {
                          setDialog({ kind: "delete", record });
                        }}
                      />
                    </>
                  )}
                  {/* Past the last page (its last record deleted), Previous stays reachable. */}
                  {(listing.records.length > 0 || page > 1) && (
                    <nav aria-label={t("pagination.records")}>
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
                  )}
                </>
              )}
              <SnapshotsPanel
                snapshots={snapshots?.key === snapshotsKey ? snapshots.list : null}
                loading={snapshots?.key !== snapshotsKey}
                readOnly={readOnly}
                busy={busy}
                onCreate={() => {
                  setDialog({ kind: "snapshot" });
                }}
                onRestore={(snapshot) => {
                  setDialog({ kind: "restore", snapshot });
                }}
              />
            </>
          )}
        </>
      )}
      {(dialog?.kind === "add" || dialog?.kind === "edit") && (
        <RecordDialog
          zone={zone}
          {...(dialog.kind === "edit" && { record: dialog.record })}
          types={types}
          busy={busy}
          onSubmit={(draft) => {
            if (dialog.kind === "add") {
              void create(draft);
              return;
            }
            void run(
              (confirmationId) => livedns.replaceRecord(account, zone, draft, confirmationId),
              t("feedback.recordUpdated", { name: draft.name, type: draft.type }),
            );
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
      {dialog?.kind === "delete" && (
        <ConfirmDialog
          title={t("dialog.deleteRecord.title")}
          body={t("dialog.deleteRecord.body", {
            name: dialog.record.name,
            type: dialog.record.type,
            zone,
          })}
          confirmLabel={t("action.delete")}
          variant="danger"
          busy={busy}
          onConfirm={() => {
            const { name, type } = dialog.record;
            void run(
              (confirmationId) => livedns.deleteRecord(account, zone, name, type, confirmationId),
              t("feedback.recordDeleted", { name, type }),
            );
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
      {dialog?.kind === "snapshot" && (
        <SnapshotDialog
          zone={zone}
          busy={busy}
          onSubmit={(name) => {
            void takeSnapshot(name);
          }}
          onCancel={() => {
            setDialog(null);
          }}
        />
      )}
      {dialog?.kind === "restore" && (
        <ConfirmDialog
          title={t("dialog.restoreSnapshot.title")}
          body={t("dialog.restoreSnapshot.body", { name: dialog.snapshot.name, zone })}
          confirmLabel={t("action.restore")}
          variant="warning"
          busy={busy}
          onConfirm={() => {
            const { id: snapshotId, name } = dialog.snapshot;
            void run(
              (confirmationId) =>
                livedns.restoreSnapshot(account, zone, snapshotId, confirmationId),
              t("feedback.snapshotRestored", { name }),
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
