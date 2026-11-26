// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["node_modules", "coverage", "dist"] },
  js.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
    },
  },
  {
    files: ["tests/**"],
    rules: { "@typescript-eslint/no-non-null-assertion": "off" },
  },
  { files: ["**/*.js", "**/*.mjs"], ...tseslint.configs.disableTypeChecked },
);
