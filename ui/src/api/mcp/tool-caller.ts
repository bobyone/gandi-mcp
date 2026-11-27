// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import type { PendingConfirmation } from "../pending-confirmation";

/** The part of the MCP App connection used to call the tools of the server. */
export interface ToolCaller {
  callServerTool(params: { name: string; arguments: Record<string, unknown> }): Promise<{
    isError?: boolean | undefined;
    structuredContent?: unknown;
    content?: unknown[] | undefined;
  }>;
}

/** Builds the error of a notion from a message already explained for the user. */
export type ErrorFactory = (message: string) => Error;

function errorText(content: unknown[] | undefined): string {
  const block = content?.find(
    (item): item is { type: "text"; text: string } =>
      typeof item === "object" &&
      item !== null &&
      (item as { type?: unknown }).type === "text" &&
      typeof (item as { text?: unknown }).text === "string",
  );
  return block?.text ?? "";
}

/**
 * Call a tool and return its structured result; a refusal or a transport failure
 * rejects with the error built by `failure`.
 */
export async function callTool(
  caller: ToolCaller,
  name: string,
  args: Record<string, unknown>,
  failure: ErrorFactory,
): Promise<Record<string, unknown>> {
  let result;
  try {
    result = await caller.callServerTool({ name, arguments: args });
  } catch (error) {
    throw failure(error instanceof Error ? error.message : String(error));
  }
  const data = result.structuredContent;
  if (result.isError === true || typeof data !== "object" || data === null) {
    throw failure(errorText(result.content));
  }
  return data as Record<string, unknown>;
}

/** The pending confirmation a tool result describes, if any. */
export function pendingOf(result: Record<string, unknown>): PendingConfirmation | null {
  return result.status === "confirmation_pending"
    ? { confirmationId: String(result.confirmation_id) }
    : null;
}
