// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import { beforeAll, describe, expect, it, vi } from "vitest";
import type { Account } from "../../../src/api/account";
import type { AccountsApi } from "../../../src/api/accounts-api";
import {
  LiveDnsError,
  type DnsRecord,
  type RecordPage,
  type Snapshot,
} from "../../../src/api/livedns";
import type { LiveDnsApi } from "../../../src/api/livedns-api";
import { ZoneScreen } from "../../../src/components/livedns/zone-screen";
import { createI18n } from "../../../src/i18n/i18n";

const PERSO: Account = {
  name: "Perso",
  environment: "sandbox",
  readOnly: false,
  isDefault: true,
  removalPending: false,
  payingOrganization: null,
};
const WATCH: Account = { ...PERSO, name: "Watch", readOnly: true, isDefault: false };
const DKIM = `"v=DKIM1; p=${"A".repeat(400)}"`;
const WWW: DnsRecord = { name: "www", type: "A", ttl: 300, values: ["192.0.2.1", "192.0.2.2"] };
const KEY: DnsRecord = { name: "default._domainkey", type: "TXT", ttl: null, values: [DKIM] };
const BEFORE: Snapshot = {
  id: "snap-1",
  name: "before",
  automatic: false,
  createdAt: "2026-11-28T06:49:28Z",
};
const PENDING = { confirmationId: "c-1" };

let i18n: I18n;

beforeAll(async () => {
  i18n = await createI18n("en");
});

function page(records: DnsRecord[], total: number | null = records.length): RecordPage {
  return { records, page: 1, perPage: 25, total };
}

function fakeAccounts(accounts: Account[] = [PERSO, WATCH]) {
  return {
    list: vi.fn<AccountsApi["list"]>().mockResolvedValue(accounts),
    add: vi.fn<AccountsApi["add"]>(),
    update: vi.fn<AccountsApi["update"]>(),
    replaceToken: vi.fn<AccountsApi["replaceToken"]>(),
    changeEnvironment: vi.fn<AccountsApi["changeEnvironment"]>(),
    remove: vi.fn<AccountsApi["remove"]>(),
    organizations: vi.fn<AccountsApi["organizations"]>(),
    setPayingOrganization: vi.fn<AccountsApi["setPayingOrganization"]>(),
  } satisfies AccountsApi;
}

function fakeLiveDns(listing: RecordPage = page([KEY, WWW])) {
  return {
    domains: vi.fn<LiveDnsApi["domains"]>().mockResolvedValue(["example.com", "example.org"]),
    recordTypes: vi.fn<LiveDnsApi["recordTypes"]>().mockResolvedValue(["A", "MX", "TXT"]),
    records: vi.fn<LiveDnsApi["records"]>().mockResolvedValue(listing),
    createRecord: vi.fn<LiveDnsApi["createRecord"]>().mockResolvedValue("created"),
    replaceRecord: vi.fn<LiveDnsApi["replaceRecord"]>().mockResolvedValue(null),
    deleteRecord: vi.fn<LiveDnsApi["deleteRecord"]>().mockResolvedValue(null),
    snapshots: vi.fn<LiveDnsApi["snapshots"]>().mockResolvedValue([BEFORE]),
    createSnapshot: vi.fn<LiveDnsApi["createSnapshot"]>().mockResolvedValue(undefined),
    restoreSnapshot: vi.fn<LiveDnsApi["restoreSnapshot"]>().mockResolvedValue(null),
  } satisfies LiveDnsApi;
}

function show(livedns: LiveDnsApi, accounts: AccountsApi = fakeAccounts()) {
  render(
    <I18nextProvider i18n={i18n}>
      <ZoneScreen livedns={livedns} accounts={accounts} />
    </I18nextProvider>,
  );
  return userEvent.setup();
}

describe("ZoneScreen", () => {
  it("lists the records of the first zone of the default account, values in full", async () => {
    const livedns = fakeLiveDns();
    show(livedns);

    const rows = await screen.findAllByRole("row");
    expect(within(rows[1]!).getByRole("rowheader")).toHaveTextContent("default._domainkey");
    expect(within(rows[1]!).getByText(DKIM)).toBeInTheDocument();
    expect(within(rows[1]!).getByText("None")).toBeInTheDocument();
    expect(within(rows[2]!).getByText("192.0.2.2")).toBeInTheDocument();
    expect(screen.getByText("2 records")).toBeInTheDocument();
    expect(livedns.records).toHaveBeenCalledWith("Perso", "example.com", 1, 25, "");
    expect(await screen.findByRole("rowheader", { name: "before" })).toBeInTheDocument();
    expect(livedns.snapshots).toHaveBeenCalledWith("Perso", "example.com");
  });

  it("filters by type, changes the zone and goes from page to page", async () => {
    const livedns = fakeLiveDns(page([WWW], 30));
    const user = show(livedns);

    expect(await screen.findByText("Page 1 of 2")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Type"), "MX");
    await waitFor(() => {
      expect(livedns.records).toHaveBeenLastCalledWith("Perso", "example.com", 1, 25, "MX");
    });
    await user.selectOptions(screen.getByLabelText("LiveDNS domain"), "example.org");
    await waitFor(() => {
      expect(livedns.records).toHaveBeenLastCalledWith("Perso", "example.org", 1, 25, "MX");
    });
    await user.click(await screen.findByLabelText("Next page"));
    await waitFor(() => {
      expect(livedns.records).toHaveBeenLastCalledWith("Perso", "example.org", 2, 25, "MX");
    });
  });

  it("goes back to the last page when the only record of a page is deleted", async () => {
    const livedns = fakeLiveDns(page([WWW], 26));
    const user = show(livedns);

    await user.click(await screen.findByLabelText("Next page"));
    expect(await screen.findByText("Page 2 of 2")).toBeInTheDocument();
    livedns.records.mockImplementation((_account, _zone, number) =>
      Promise.resolve(number === 2 ? page([], 25) : { ...page([KEY], 25), page: 1 }),
    );
    await user.click(screen.getByRole("button", { name: "Delete www A" }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }),
    );

    expect(await screen.findByText("Page 1 of 1")).toBeInTheDocument();
    expect(
      await screen.findByRole("rowheader", { name: "default._domainkey" }),
    ).toBeInTheDocument();
    expect(livedns.records).toHaveBeenLastCalledWith("Perso", "example.com", 1, 25, "");
  });

  it("keeps Previous after an empty page when the total is unknown", async () => {
    const full = Array.from({ length: 25 }, (_, i) => ({ ...WWW, name: `h${i}` }));
    const livedns = fakeLiveDns(page(full, null));
    const user = show(livedns);

    const next = await screen.findByLabelText("Next page");
    livedns.records.mockResolvedValue({ ...page([], null), page: 2 });
    await user.click(next);
    expect(await screen.findByText("No record.")).toBeInTheDocument();
    expect(screen.getByText("Page 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Next page").closest("li")).toHaveClass("disabled");
    livedns.records.mockResolvedValue(page(full, null));
    await user.click(screen.getByLabelText("Previous page"));

    expect(await screen.findByText("Page 1")).toBeInTheDocument();
    expect(livedns.records).toHaveBeenLastCalledWith("Perso", "example.com", 1, 25, "");
  });

  it("adds a record and reports an identical one", async () => {
    const livedns = fakeLiveDns();
    const user = show(livedns);

    await user.click(await screen.findByRole("button", { name: "Add record" }));
    const dialog = within(await screen.findByRole("dialog"));
    await user.click(dialog.getByRole("button", { name: "Save" }));
    expect(dialog.getByText(/Enter a name without spaces/)).toBeInTheDocument();
    await user.type(dialog.getByLabelText("Name"), "mail");
    await user.selectOptions(dialog.getByLabelText("Type"), "MX");
    await user.type(dialog.getByLabelText("TTL (seconds)"), "10");
    await user.type(dialog.getByLabelText("Values"), "10 spool.mail.gandi.net.");
    await user.click(dialog.getByRole("button", { name: "Save" }));
    expect(livedns.createRecord).not.toHaveBeenCalled();
    await user.clear(dialog.getByLabelText("TTL (seconds)"));
    await user.click(dialog.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("The record mail MX is created.")).toBeInTheDocument();
    expect(livedns.createRecord).toHaveBeenCalledWith("Perso", "example.com", {
      name: "mail",
      type: "MX",
      ttl: null,
      values: ["10 spool.mail.gandi.net."],
    });
    await waitFor(() => {
      expect(livedns.records).toHaveBeenCalledTimes(2);
    });

    livedns.createRecord.mockResolvedValue("unchanged");
    await user.click(screen.getByRole("button", { name: "Add record" }));
    const again = within(await screen.findByRole("dialog"));
    await user.type(again.getByLabelText("Name"), "www");
    await user.type(again.getByLabelText("Values"), "192.0.2.1");
    await user.click(again.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(/already exists with these values/)).toBeInTheDocument();
  });

  it("edits a record after the server confirmation", async () => {
    const livedns = fakeLiveDns();
    livedns.replaceRecord.mockResolvedValueOnce(PENDING);
    const user = show(livedns);

    await user.click(await screen.findByRole("button", { name: "Edit www A" }));
    const dialog = within(await screen.findByRole("dialog"));
    expect(dialog.getByLabelText("Name")).toHaveAttribute("readonly");
    expect(dialog.getByLabelText("Type")).toBeDisabled();
    expect(dialog.getByLabelText("Values")).toHaveValue("192.0.2.1\n192.0.2.2");
    await user.clear(dialog.getByLabelText("Values"));
    await user.type(dialog.getByLabelText("Values"), "192.0.2.9");
    await user.click(dialog.getByRole("button", { name: "Save" }));

    expect(await screen.findByText(/Confirm or refuse this operation/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(await screen.findByText("The record www A is updated.")).toBeInTheDocument();
    const draft = { name: "www", type: "A", ttl: 300, values: ["192.0.2.9"] };
    expect(livedns.replaceRecord.mock.calls).toEqual([
      ["Perso", "example.com", draft, undefined],
      ["Perso", "example.com", draft, "c-1"],
    ]);
  });

  it("deletes a record once previewed, and explains a failure", async () => {
    const livedns = fakeLiveDns();
    livedns.deleteRecord.mockRejectedValueOnce(new LiveDnsError("The record does not exist."));
    const user = show(livedns);

    await user.click(await screen.findByRole("button", { name: "Delete www A" }));
    const dialog = within(await screen.findByRole("dialog"));
    expect(dialog.getByText(/The A record of www in example.com/)).toBeInTheDocument();
    await user.click(dialog.getByRole("button", { name: "Cancel" }));
    expect(livedns.deleteRecord).not.toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Delete www A" }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }),
    );
    expect(await screen.findByText("The record does not exist.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Delete www A" }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Delete" }),
    );
    expect(await screen.findByText("The record www A is deleted.")).toBeInTheDocument();
  });

  it("creates and restores snapshots", async () => {
    const livedns = fakeLiveDns();
    livedns.restoreSnapshot.mockResolvedValueOnce(PENDING);
    const user = show(livedns);

    await user.click(await screen.findByRole("button", { name: "Create snapshot" }));
    const dialog = within(await screen.findByRole("dialog"));
    await user.type(dialog.getByLabelText("Snapshot name"), " test ");
    await user.click(dialog.getByRole("button", { name: "Create snapshot" }));
    expect(await screen.findByText("The snapshot is created.")).toBeInTheDocument();
    expect(livedns.createSnapshot).toHaveBeenCalledWith("Perso", "example.com", "test");

    await user.click(await screen.findByRole("button", { name: "Restore before" }));
    const restore = within(await screen.findByRole("dialog"));
    expect(restore.getByText(/Every record of example.com/)).toBeInTheDocument();
    await user.click(restore.getByRole("button", { name: "Restore" }));
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(await screen.findByText("The snapshot before is restored.")).toBeInTheDocument();
    expect(livedns.restoreSnapshot).toHaveBeenLastCalledWith(
      "Perso",
      "example.com",
      "snap-1",
      "c-1",
    );
  });

  it("offers no change on a read-only account", async () => {
    const livedns = fakeLiveDns();
    const user = show(livedns);

    await screen.findByRole("rowheader", { name: "www" });
    await user.selectOptions(screen.getByLabelText("Account"), "Watch");

    expect(await screen.findByText("Read-only")).toBeInTheDocument();
    await waitFor(() => {
      expect(livedns.records).toHaveBeenLastCalledWith("Watch", "example.com", 1, 25, "");
    });
    expect(await screen.findByRole("rowheader", { name: "www" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add record" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Edit/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Create snapshot" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Restore/ })).not.toBeInTheDocument();
  });

  it("explains a missing account, an account without zone and empty lists", async () => {
    const { unmount } = render(
      <I18nextProvider i18n={i18n}>
        <ZoneScreen livedns={fakeLiveDns()} accounts={fakeAccounts([])} />
      </I18nextProvider>,
    );
    expect(await screen.findByText(/Add a Gandi account first/)).toBeInTheDocument();
    unmount();

    const none = fakeLiveDns();
    none.domains.mockResolvedValue([]);
    const shown = render(
      <I18nextProvider i18n={i18n}>
        <ZoneScreen livedns={none} accounts={fakeAccounts()} />
      </I18nextProvider>,
    );
    expect(await screen.findByText("This account has no domain on LiveDNS.")).toBeInTheDocument();
    shown.unmount();

    const empty = fakeLiveDns(page([], null));
    empty.snapshots.mockResolvedValue([]);
    empty.recordTypes.mockRejectedValue(new Error("down"));
    show(empty);
    expect(await screen.findByText("No record.")).toBeInTheDocument();
    expect(await screen.findByText("No snapshot.")).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "CNAME" })).toBeInTheDocument();
  });

  it("shows the server explanation when a list fails", async () => {
    const livedns = fakeLiveDns();
    livedns.domains.mockRejectedValue(new LiveDnsError("LiveDNS is not available."));
    show(livedns);

    expect(await screen.findByText("LiveDNS is not available.")).toBeInTheDocument();
  });
});
