// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { useCallback, useState } from "react";
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
  const ask = useCallback(
    async (fqdn: string) => {
      setState({ kind: "loading" });
      try {
        setState({ kind: "ready", quote: await api.quote(account, fqdn, procedure) });
      } catch (error) {
        setState({
          kind: "failed",
          message: error instanceof DomainsError ? error.message : "",
        });
      }
    },
    [api, account, procedure],
  );
  const reset = useCallback(() => {
    setState({ kind: "idle" });
  }, []);
  return { state, ask, reset };
}
