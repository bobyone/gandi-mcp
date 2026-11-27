// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later

/** A Gandi organization of an account; its name is untrusted data, shown as text only. */
export interface Organization {
  readonly id: string;
  readonly name: string;
  /** Gandi kind of organization (individual, company...), untrusted. */
  readonly type: string;
}
