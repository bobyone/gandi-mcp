// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId } from "react";
import Button from "react-bootstrap/Button";
import Spinner from "react-bootstrap/Spinner";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";
import type { Snapshot } from "../../api/livedns";
import { formatDateTime } from "../domains/format";

export interface SnapshotsPanelProps {
  /** The latest snapshots, null while they load or when they could not be read. */
  readonly snapshots: readonly Snapshot[] | null;
  readonly loading: boolean;
  readonly readOnly: boolean;
  readonly busy: boolean;
  readonly onCreate: () => void;
  readonly onRestore: (snapshot: Snapshot) => void;
}

/** The latest snapshots of a zone, newest first, with create and restore. */
export function SnapshotsPanel(props: SnapshotsPanelProps) {
  const { snapshots, loading, readOnly, busy, onCreate, onRestore } = props;
  const { t, i18n } = useTranslation();
  const id = useId();
  return (
    <section aria-labelledby={`${id}-title`} className="mt-4">
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-2 mb-2">
        <h2 id={`${id}-title`} className="h5 mb-0">
          {t("zone.snapshots")}
        </h2>
        {!readOnly && (
          <Button variant="outline-primary" disabled={busy} onClick={onCreate}>
            {t("action.createSnapshot")}
          </Button>
        )}
      </div>
      {loading ? (
        <div role="status">
          <Spinner animation="border" size="sm" className="me-2" aria-hidden="true" />
          {t("zone.snapshotsLoading")}
        </div>
      ) : snapshots === null ? null : snapshots.length === 0 ? (
        <p>{t("zone.snapshotsEmpty")}</p>
      ) : (
        <Table responsive hover className="align-middle">
          <thead>
            <tr>
              <th scope="col">{t("field.snapshotName")}</th>
              <th scope="col">{t("column.createdAt")}</th>
              <th scope="col">{t("column.automatic")}</th>
              {!readOnly && (
                <th scope="col">
                  <span className="visually-hidden">{t("column.actions")}</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {snapshots.map((snapshot) => (
              <tr key={snapshot.id}>
                <th scope="row" className="text-break">
                  {snapshot.name}
                </th>
                <td>{formatDateTime(snapshot.createdAt, i18n.language) ?? t("details.none")}</td>
                <td>
                  {snapshot.automatic === null
                    ? t("details.none")
                    : snapshot.automatic
                      ? t("value.yes")
                      : t("value.no")}
                </td>
                {!readOnly && (
                  <td className="text-end">
                    <Button
                      variant="outline-warning"
                      size="sm"
                      disabled={busy}
                      aria-label={t("action.restoreFor", { name: snapshot.name })}
                      onClick={() => {
                        onRestore(snapshot);
                      }}
                    >
                      {t("action.restore")}
                    </Button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </Table>
      )}
    </section>
  );
}
