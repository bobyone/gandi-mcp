// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import Button from "react-bootstrap/Button";
import Table from "react-bootstrap/Table";
import { useTranslation } from "react-i18next";
import type { DnsRecord } from "../../api/livedns";

export interface RecordTableProps {
  readonly records: readonly DnsRecord[];
  readonly readOnly: boolean;
  readonly busy: boolean;
  readonly onEdit: (record: DnsRecord) => void;
  readonly onDelete: (record: DnsRecord) => void;
}

/** The records of a page; long values (DKIM keys) wrap, shown as text only. */
export function RecordTable({ records, readOnly, busy, onEdit, onDelete }: RecordTableProps) {
  const { t, i18n } = useTranslation();
  const seconds = new Intl.NumberFormat(i18n.language);
  return (
    <Table responsive hover className="align-middle">
      <thead>
        <tr>
          <th scope="col">{t("field.recordName")}</th>
          <th scope="col">{t("field.recordType")}</th>
          <th scope="col">{t("field.ttl")}</th>
          <th scope="col">{t("field.recordValues")}</th>
          {!readOnly && (
            <th scope="col">
              <span className="visually-hidden">{t("column.actions")}</span>
            </th>
          )}
        </tr>
      </thead>
      <tbody>
        {records.map((item) => {
          const label = { name: item.name, type: item.type };
          return (
            <tr key={`${item.name} ${item.type}`}>
              <th scope="row" className="text-break">
                {item.name}
              </th>
              <td>{item.type}</td>
              <td>{item.ttl !== null ? seconds.format(item.ttl) : t("details.none")}</td>
              <td className="text-break font-monospace small">
                {item.values.map((value) => (
                  <div key={value}>{value}</div>
                ))}
              </td>
              {!readOnly && (
                <td className="text-end text-nowrap">
                  <Button
                    variant="outline-secondary"
                    size="sm"
                    className="me-2"
                    disabled={busy}
                    aria-label={t("action.editFor", label)}
                    onClick={() => {
                      onEdit(item);
                    }}
                  >
                    {t("action.edit")}
                  </Button>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    disabled={busy}
                    aria-label={t("action.deleteFor", label)}
                    onClick={() => {
                      onDelete(item);
                    }}
                  >
                    {t("action.delete")}
                  </Button>
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </Table>
  );
}
