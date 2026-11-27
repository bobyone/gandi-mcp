// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useId } from "react";
import Form from "react-bootstrap/Form";
import { useTranslation } from "react-i18next";
import { MAX_YEARS, MIN_YEARS, bandFor, durations, type Quote } from "../../api/domain";
import { formatPrice } from "./format";

export interface DurationPriceProps {
  readonly quote: Quote;
  readonly years: number;
  readonly onChange: (years: number) => void;
}

/** All durations accepted by the server, when Gandi gives no band. */
const ALL_YEARS = Array.from({ length: MAX_YEARS - MIN_YEARS + 1 }, (_, i) => MIN_YEARS + i);

/** Choose a duration and show the indicative price Gandi announces for it. */
export function DurationPrice({ quote, years, onChange }: DurationPriceProps) {
  const { t, i18n } = useTranslation();
  const id = useId();
  const offered = durations(quote);
  const choices = offered.length > 0 ? offered : ALL_YEARS;
  const band = bandFor(quote, years);
  const price =
    band && quote.currency !== null
      ? formatPrice(band.perYearAfterTaxes, quote.currency, i18n.language)
      : null;
  return (
    <>
      <Form.Group controlId={`${id}-duration`} className="mb-3">
        <Form.Label>{t("field.duration")}</Form.Label>
        <Form.Select
          value={years}
          onChange={(event) => {
            onChange(Number(event.target.value));
          }}
        >
          {choices.map((choice) => (
            <option key={choice} value={choice}>
              {t("duration.years", { count: choice })}
            </option>
          ))}
        </Form.Select>
      </Form.Group>
      <p className="mb-1 fw-semibold">{price ? t("price.perYear", { price }) : t("price.none")}</p>
      <p className="text-body-secondary small">{t("price.notice")}</p>
    </>
  );
}
