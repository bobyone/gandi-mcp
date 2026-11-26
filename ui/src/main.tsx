// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import "bootstrap/dist/css/bootstrap.min.css";
import "./theme.css";
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { GandiApp } from "./gandi-app";

function Root() {
  const { app, error } = useApp({
    appInfo: { name: "gandi-mcp", version: "0.1.0" },
    capabilities: {},
  });
  return <GandiApp app={app} error={error} />;
}

const container = document.getElementById("root");
if (container) {
  createRoot(container).render(
    <StrictMode>
      <Root />
    </StrictMode>,
  );
}
