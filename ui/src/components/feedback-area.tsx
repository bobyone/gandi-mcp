// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/Button";
import { useTranslation } from "react-i18next";

export type Feedback = { variant: "success" | "danger"; text: string };

export interface FeedbackAreaProps {
  /** A confirmation asked by the server is waiting: offer to continue once answered. */
  readonly pending: boolean;
  readonly feedback: Feedback | null;
  readonly busy: boolean;
  readonly onContinue: () => void;
  readonly onDismiss: () => void;
}

/** Live area of a screen: the pending confirmation and the outcome of the last action. */
export function FeedbackArea({
  pending,
  feedback,
  busy,
  onContinue,
  onDismiss,
}: FeedbackAreaProps) {
  const { t } = useTranslation();
  return (
    <div aria-live="polite">
      {pending && (
        <Alert variant="info">
          <p className="mb-2">{t("feedback.confirmPending")}</p>
          <Button variant="primary" disabled={busy} onClick={onContinue}>
            {t("action.continue")}
          </Button>
        </Alert>
      )}
      {feedback && (
        <Alert
          variant={feedback.variant}
          dismissible
          closeLabel={t("action.close")}
          onClose={onDismiss}
        >
          {feedback.text}
        </Alert>
      )}
    </div>
  );
}
