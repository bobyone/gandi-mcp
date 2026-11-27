// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type { App } from "@modelcontextprotocol/ext-apps";
import { useHostStyles } from "@modelcontextprotocol/ext-apps/react";
import type { i18n as I18n } from "i18next";
import { useEffect, useMemo, useState } from "react";
import Alert from "react-bootstrap/Alert";
import Tab from "react-bootstrap/Tab";
import Tabs from "react-bootstrap/Tabs";
import { I18nextProvider } from "react-i18next";
import { McpAccountsApi } from "./api/mcp/mcp-accounts-api";
import { McpDomainsApi } from "./api/mcp/mcp-domains-api";
import { AccountsScreen } from "./components/accounts/accounts-screen";
import { DomainsScreen } from "./components/domains/domains-screen";
import { createI18n, negotiate } from "./i18n/i18n";

export interface GandiAppProps {
  /** The connected MCP App, or null while connecting. */
  readonly app: App | null;
  readonly error: Error | null;
}

/** Root of the MCP App: host theme and language, then the accounts and domains tabs. */
export function GandiApp({ app, error }: GandiAppProps) {
  const context = app?.getHostContext();
  useHostStyles(app, context ?? null);
  const language = negotiate([context?.locale, ...navigator.languages]);
  const [i18n, setI18n] = useState<I18n | null>(null);

  useEffect(() => {
    let active = true;
    void createI18n(language).then((instance) => {
      if (active) setI18n(instance);
    });
    return () => {
      active = false;
    };
  }, [language]);

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dataset.bsTheme = context?.theme === "dark" ? "dark" : "light";
  }, [language, context?.theme]);

  const api = useMemo(
    () => (app ? { accounts: new McpAccountsApi(app), domains: new McpDomainsApi(app) } : null),
    [app],
  );

  if (i18n === null) return null;
  return (
    <I18nextProvider i18n={i18n}>
      {error ? (
        <Alert variant="danger" className="m-3">
          {i18n.t("app.connectionFailed")}
        </Alert>
      ) : api === null ? (
        <p role="status" className="m-3">
          {i18n.t("app.connecting")}
        </p>
      ) : (
        <Tabs defaultActiveKey="accounts" mountOnEnter unmountOnExit className="px-3 pt-2">
          <Tab eventKey="accounts" title={i18n.t("tab.accounts")}>
            <AccountsScreen api={api.accounts} />
          </Tab>
          <Tab eventKey="domains" title={i18n.t("tab.domains")}>
            <DomainsScreen domains={api.domains} accounts={api.accounts} />
          </Tab>
        </Tabs>
      )}
    </I18nextProvider>
  );
}
