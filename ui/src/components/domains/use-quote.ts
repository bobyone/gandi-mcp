// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useRef, useState } from "react";
import { DomainsError, type Procedure, type Quote } from "../../api/domain";
import type { DomainsApi } from "../../api/domains-api";

export type QuoteState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; quote: Quote }
  | { kind: "failed"; message: string };

/** Ask Gandi for a quote and follow its state; a failure keeps the server message. */
export function useQuote(api: DomainsApi, account: string, procedure: Procedure) {
  const [state, setState] = useState<QuoteState>({ kind: "idle" });
  /** Identifies the latest request: an older answer, or one asked before a reset, is ignored. */
  const latest = useRef(0);
  const ask = useCallback(
    async (fqdn: string) => {
      const request = ++latest.current;
      setState({ kind: "loading" });
      let next: QuoteState;
      try {
        next = { kind: "ready", quote: await api.quote(account, fqdn, procedure) };
      } catch (error) {
        next = { kind: "failed", message: error instanceof DomainsError ? error.message : "" };
      }
      if (request === latest.current) setState(next);
    },
    [api, account, procedure],
  );
  const reset = useCallback(() => {
    latest.current += 1;
    setState({ kind: "idle" });
  }, []);
  return { state, ask, reset };
}
