// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { viteSingleFile } from "vite-plugin-singlefile";

const outDir = "../src/gandi_mcp/protocol/app/static";

export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: {
    outDir,
    emptyOutDir: false,
    rolldownOptions: { input: "app.html" },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["tests/setup.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"],
      thresholds: { lines: 90, functions: 90, branches: 90, statements: 90 },
    },
  },
});
