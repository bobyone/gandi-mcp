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
  DomainsError,
  type DomainDetails,
  type DomainPage,
  type DomainSummary,
  type Quote,
} from "../../../src/api/domain";
import type { DomainsApi } from "../../../src/api/domains-api";
import { DomainsScreen } from "../../../src/components/domains/domains-screen";
import { createI18n } from "../../../src/i18n/i18n";

const PERSO: Account = {
  name: "Perso",
  environment: "sandbox",
  readOnly: false,
  isDefault: false,
  removalPending: false,
  payingOrganization: null,
};
const PRO: Account = { ...PERSO, name: "Pro", isDefault: true };
const LOCKED: Account = { ...PERSO, name: "Locked", readOnly: true };

const CAFE: DomainSummary = {
  fqdn: "xn--caf-dma.fr",
  displayName: "café.fr",
  expiresAt: "2027-03-01T12:00:00Z",
  autorenew: true,
  transferLock: true,
  statuses: ["clientTransferProhibited"],
};
const SHOP: DomainSummary = {
  fqdn: "shop.com",
  displayName: "shop.com",
  expiresAt: null,
  autorenew: false,
  transferLock: false,
  statuses: [],
};
const DETAILS: DomainDetails = {
  ...CAFE,
  createdAt: "2020-01-01T00:00:00Z",
  nameservers: ["ns1.gandi.net", "ns2.gandi.net"],
  tags: ["perso"],
  contacts: [
    {
      role: "owner",
      fields: [
        { field: "given", value: "Ada" },
        { field: "email", value: "ada@example.com" },
      ],
    },
    { role: "admin", fields: [{ field: "country", value: "FR" }] },
    { role: "tech", fields: [{ field: "city", value: "Paris" }] },
    { role: "bill", fields: [{ field: "zip", value: "75002" }] },
  ],
};
const QUOTE: Quote = {
  status: "available",
  currency: "EUR",
  bands: [{ minYears: 1, maxYears: 10, perYearAfterTaxes: 12 }],
};
const PENDING = { confirmationId: "c-1" };

let i18n: I18n;

beforeAll(async () => {
  i18n = await createI18n("en");
});

function page(domains: DomainSummary[], total: number | null = domains.length): DomainPage {
  return { domains, page: 1, perPage: 25, total };
}

function fakeAccounts(accounts: Account[] = [PERSO, PRO]) {
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

function fakeDomains(listing: DomainPage = page([CAFE, SHOP])) {
  return {
    list: vi.fn<DomainsApi["list"]>().mockResolvedValue(listing),
    details: vi.fn<DomainsApi["details"]>().mockResolvedValue(DETAILS),
    quote: vi.fn<DomainsApi["quote"]>().mockResolvedValue(QUOTE),
    setAutorenew: vi.fn<DomainsApi["setAutorenew"]>().mockResolvedValue(null),
    setTransferLock: vi.fn<DomainsApi["setTransferLock"]>().mockResolvedValue(null),
    setNameservers: vi.fn<DomainsApi["setNameservers"]>().mockResolvedValue(null),
    renew: vi.fn<DomainsApi["renew"]>().mockResolvedValue(null),
    register: vi.fn<DomainsApi["register"]>().mockResolvedValue(null),
  } satisfies DomainsApi;
}

function show(domains: DomainsApi, accounts: AccountsApi = fakeAccounts()) {
  render(
    <I18nextProvider i18n={i18n}>
      <DomainsScreen domains={domains} accounts={accounts} />
    </I18nextProvider>,
  );
  return userEvent.setup();
}

async function openDetails(user: ReturnType<typeof userEvent.setup>, name = "café.fr") {
  await user.click(await screen.findByRole("button", { name: `Details of ${name}` }));
  return within(await screen.findByRole("dialog"));
}

describe("DomainsScreen", () => {
  it("lists the domains of the default account", async () => {
    const domains = fakeDomains();
    show(domains);

    const rows = await screen.findAllByRole("row");
    expect(rows).toHaveLength(3);
    const cafe = within(rows[1]!);
    expect(cafe.getByRole("rowheader")).toHaveTextContent("café.fr");
    expect(cafe.getByText("clientTransferProhibited")).toBeInTheDocument();
    expect(cafe.getAllByText("On")).toHaveLength(2);
    expect(within(rows[2]!).getAllByText("Off")).toHaveLength(2);
    expect(within(rows[2]!).getByText("None")).toBeInTheDocument();
    expect(screen.getByText("2 domains")).toBeInTheDocument();
    expect(screen.getByText("Page 1 of 1")).toBeInTheDocument();
    expect(domains.list).toHaveBeenCalledWith("Pro", 1, 25, "");
  });

  it("filters by name and changes the account", async () => {
    const domains = fakeDomains();
    const user = show(domains);

    await user.type(await screen.findByLabelText("Filter by name"), " *.fr ");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => {
      expect(domains.list).toHaveBeenLastCalledWith("Pro", 1, 25, "*.fr");
    });
    await user.selectOptions(screen.getByLabelText("Account"), "Perso");
    await waitFor(() => {
      expect(domains.list).toHaveBeenLastCalledWith("Perso", 1, 25, "*.fr");
    });
  });

  it("goes from page to page", async () => {
    const domains = fakeDomains(page([CAFE], 30));
    const user = show(domains);

    expect(await screen.findByText("Page 1 of 2")).toBeInTheDocument();
    expect(screen.getByText("30 domains")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Next page"));
    await waitFor(() => {
      expect(domains.list).toHaveBeenLastCalledWith("Pro", 2, 25, "");
    });
    expect(await screen.findByText("Page 2 of 2")).toBeInTheDocument();
    await user.click(screen.getByLabelText("Previous page"));
    await waitFor(() => {
      expect(domains.list).toHaveBeenLastCalledWith("Pro", 1, 25, "");
    });
  });

  it("offers the next page while pages are full when the total is unknown", async () => {
    const full = Array.from({ length: 25 }, (_, i) => ({ ...SHOP, fqdn: `s${i}.com` }));
    const domains = fakeDomains(page(full, null));
    const user = show(domains);

    expect(await screen.findByText("Page 1")).toBeInTheDocument();
    domains.list.mockResolvedValue({ ...page([SHOP], null), page: 2 });
    await user.click(screen.getByLabelText("Next page"));
    expect(await screen.findByText("Page 2")).toBeInTheDocument();
    expect(screen.getByLabelText("Next page").closest("li")).toHaveClass("disabled");
  });

  it("explains an empty list, a missing account and failures", async () => {
    const domains = fakeDomains(page([]));
    show(domains);
    expect(await screen.findByText("No domain matches.")).toBeInTheDocument();
  });

  it("asks for an account first", async () => {
    show(fakeDomains(), fakeAccounts([]));

    expect(await screen.findByText(/Add a Gandi account first/)).toBeInTheDocument();
  });

  it("shows the server explanation when listing fails", async () => {
    const accounts = fakeAccounts();
    accounts.list.mockRejectedValue(new Error("keyring"));
    show(fakeDomains(), accounts);
    expect(await screen.findByRole("alert")).toHaveTextContent("keyring");
  });

  it("shows the explanation of a refused listing", async () => {
    const domains = fakeDomains();
    domains.list.mockRejectedValue(new DomainsError("The token cannot read domains."));
    show(domains);

    expect(await screen.findByRole("alert")).toHaveTextContent("The token cannot read domains.");
  });

  it("falls back to a generic message", async () => {
    const domains = fakeDomains();
    domains.list.mockRejectedValue("odd");
    show(domains);

    expect(await screen.findByRole("alert")).toHaveTextContent("The operation failed");
  });

  it("shows the details of a domain with its contacts", async () => {
    const domains = fakeDomains();
    const user = show(domains);

    const dialog = await openDetails(user);

    expect(await dialog.findByText("Domain café.fr")).toBeInTheDocument();
    expect(dialog.getByText("ns2.gandi.net")).toBeInTheDocument();
    expect(dialog.getByText("perso")).toBeInTheDocument();
    for (const role of ["Owner", "Admin contact", "Tech contact", "Billing contact"])
      expect(dialog.getByRole("heading", { name: role })).toBeInTheDocument();
    expect(dialog.getByText("ada@example.com")).toBeInTheDocument();
    expect(dialog.getByText("Email address")).toBeInTheDocument();
    expect(domains.details).toHaveBeenCalledWith("Pro", "xn--caf-dma.fr");
    await user.click(dialog.getAllByRole("button", { name: "Close" })[1]!);
    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
  });

  it("shows details without optional data", async () => {
    const domains = fakeDomains();
    domains.details.mockResolvedValue({
      ...DETAILS,
      createdAt: null,
      autorenew: null,
      transferLock: false,
      statuses: [],
      nameservers: [],
      tags: [],
      contacts: [],
    });
    const user = show(domains);

    const dialog = await openDetails(user);

    expect(await dialog.findAllByText("None")).toHaveLength(5);
    expect(dialog.getByRole("button", { name: "Turn on automatic renewal" })).toBeInTheDocument();
    expect(dialog.getByRole("button", { name: "Lock the transfer" })).toBeInTheDocument();
  });

  it("explains why the details cannot be read", async () => {
    const domains = fakeDomains();
    domains.details.mockRejectedValueOnce(new DomainsError("Domain not found."));
    domains.details.mockRejectedValueOnce("odd");
    const user = show(domains);

    expect(await (await openDetails(user)).findByText("Domain not found.")).toBeInTheDocument();
    await user.click(screen.getAllByRole("button", { name: "Close" })[1]!);
    expect(await (await openDetails(user)).findByText("The operation failed")).toBeInTheDocument();
  });

  it("turns the automatic renewal off and reads the domain again", async () => {
    const domains = fakeDomains();
    const user = show(domains);

    const dialog = await openDetails(user);
    await user.click(await dialog.findByRole("button", { name: "Turn off automatic renewal" }));

    expect(domains.setAutorenew).toHaveBeenCalledWith("Pro", "xn--caf-dma.fr", false);
    expect(await screen.findByText("The domain café.fr is updated.")).toBeInTheDocument();
    expect(domains.details).toHaveBeenCalledTimes(2);
    await waitFor(() => {
      expect(domains.list).toHaveBeenCalledTimes(2);
    });
  });

  it("waits for the confirmation before unlocking the transfer", async () => {
    const domains = fakeDomains();
    domains.setTransferLock.mockResolvedValueOnce(PENDING).mockResolvedValueOnce(null);
    const user = show(domains);

    const dialog = await openDetails(user);
    await user.click(await dialog.findByRole("button", { name: "Unlock the transfer" }));
    expect(await screen.findByText(/Confirm or refuse this operation/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(domains.setTransferLock.mock.calls).toEqual([
      ["Pro", "xn--caf-dma.fr", false, undefined],
      ["Pro", "xn--caf-dma.fr", false, "c-1"],
    ]);
    expect(await screen.findByText("The domain café.fr is updated.")).toBeInTheDocument();
  });

  it("locks the transfer and explains a refusal", async () => {
    const domains = fakeDomains();
    domains.details.mockResolvedValue({ ...DETAILS, transferLock: false });
    domains.setTransferLock.mockRejectedValue(new DomainsError("This TLD has no lock."));
    const user = show(domains);

    const dialog = await openDetails(user);
    await user.click(await dialog.findByRole("button", { name: "Lock the transfer" }));

    expect(domains.setTransferLock).toHaveBeenCalledWith("Pro", "xn--caf-dma.fr", true, undefined);
    expect(await screen.findByText("This TLD has no lock.")).toBeInTheDocument();
  });

  it("changes the nameservers after checking them", async () => {
    const domains = fakeDomains();
    domains.setNameservers.mockResolvedValueOnce(PENDING).mockResolvedValueOnce(null);
    const user = show(domains);

    const details = await openDetails(user);
    await user.click(await details.findByRole("button", { name: "Change the nameservers" }));
    const dialog = within(await screen.findByRole("dialog"));
    const field = dialog.getByLabelText("Nameservers");
    expect(field).toHaveValue("ns1.gandi.net\nns2.gandi.net");
    await user.clear(field);
    await user.click(dialog.getByRole("button", { name: "Save" }));
    expect(dialog.getByText(/Enter 1 to 13 nameservers/)).toBeVisible();
    await user.type(field, "ns1.example.net{enter}ns2.example.net");
    await user.click(dialog.getByRole("button", { name: "Save" }));
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(domains.setNameservers.mock.calls).toEqual([
      ["Pro", "xn--caf-dma.fr", ["ns1.example.net", "ns2.example.net"], undefined],
      ["Pro", "xn--caf-dma.fr", ["ns1.example.net", "ns2.example.net"], "c-1"],
    ]);
  });

  it("cancels the nameserver change and comes back to the details", async () => {
    const user = show(fakeDomains());

    const details = await openDetails(user);
    await user.click(await details.findByRole("button", { name: "Change the nameservers" }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Cancel" }),
    );

    expect(await screen.findByText("Domain café.fr")).toBeInTheDocument();
  });

  it("renews a domain at the price shown, then confirmed by the server", async () => {
    const domains = fakeDomains();
    domains.renew.mockResolvedValueOnce(PENDING).mockResolvedValueOnce(null);
    const user = show(domains);

    const details = await openDetails(user);
    await user.click(await details.findByRole("button", { name: "Renew" }));
    const dialog = within(await screen.findByRole("dialog"));
    expect(await dialog.findByText("€12.00 per year, taxes included")).toBeInTheDocument();
    await user.selectOptions(dialog.getByLabelText("Duration"), "3");
    await user.click(dialog.getByRole("button", { name: "Renew" }));
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(domains.quote).toHaveBeenCalledWith("Pro", "xn--caf-dma.fr", "renew");
    expect(domains.renew.mock.calls).toEqual([
      ["Pro", "xn--caf-dma.fr", 3, undefined],
      ["Pro", "xn--caf-dma.fr", 3, "c-1"],
    ]);
    expect(await screen.findByText(/The order for café.fr is placed/)).toBeInTheDocument();
  });

  it("explains a renewal without price", async () => {
    const domains = fakeDomains();
    domains.quote.mockResolvedValueOnce({ status: null, currency: null, bands: [] });
    domains.quote.mockRejectedValueOnce(new DomainsError("Gandi is unavailable."));
    domains.quote.mockRejectedValueOnce("odd");
    const user = show(domains);

    const details = await openDetails(user);
    await user.click(await details.findByRole("button", { name: "Renew" }));
    let dialog = within(await screen.findByRole("dialog"));
    expect(await dialog.findByText(/Gandi announces no single price/)).toBeInTheDocument();
    expect(dialog.getAllByRole("option")).toHaveLength(10);
    await user.click(dialog.getByRole("button", { name: "Cancel" }));
    await user.click(await screen.findByRole("button", { name: "Renew" }));
    dialog = within(await screen.findByRole("dialog"));
    expect(await dialog.findByText("Gandi is unavailable.")).toBeInTheDocument();
    expect(dialog.getByRole("button", { name: "Renew" })).toBeDisabled();
    await user.click(dialog.getByRole("button", { name: "Cancel" }));
    await user.click(await screen.findByRole("button", { name: "Renew" }));
    expect(
      await within(await screen.findByRole("dialog")).findByText("The operation failed"),
    ).toBeInTheDocument();
  });

  it("offers no change on a read-only account", async () => {
    const user = show(fakeDomains(), fakeAccounts([LOCKED]));

    expect(await screen.findByText("Read-only")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Register a domain" })).not.toBeInTheDocument();
    const dialog = await openDetails(user);
    await dialog.findByText("ns1.gandi.net");
    expect(dialog.queryByRole("button", { name: "Renew" })).not.toBeInTheDocument();
  });

  it("registers a domain after the confirmation asked by the server", async () => {
    const domains = fakeDomains();
    domains.register.mockResolvedValueOnce(PENDING).mockResolvedValueOnce(null);
    const user = show(domains);

    await user.click(await screen.findByRole("button", { name: "Register a domain" }));
    const dialog = within(await screen.findByRole("dialog"));
    await user.type(dialog.getByLabelText("Domain"), "new.fr{enter}");
    await dialog.findByText("new.fr is available.");
    const typed: [string, string][] = [
      ["First name", "Ada"],
      ["Last name", "Lovelace"],
      ["Email address", "ada@example.com"],
      ["Street address", "1 rue de la Paix"],
      ["Postal code", "75002"],
      ["City", "Paris"],
      ["Country", "fr"],
    ];
    for (const [label, value] of typed) await user.type(dialog.getByLabelText(label), value);
    await user.click(dialog.getByRole("button", { name: "Register a domain" }));
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(domains.register).toHaveBeenCalledTimes(2);
    expect(domains.register.mock.calls[1]).toEqual([
      "Pro",
      "new.fr",
      1,
      expect.objectContaining({ given: "Ada", country: "fr" }),
      "c-1",
    ]);
    const done = await screen.findByText(/The order for new.fr is placed/);
    await user.click(within(done.closest(".alert")!).getByRole("button", { name: "Close" }));
    expect(screen.queryByText(/The order for new.fr is placed/)).not.toBeInTheDocument();
  });

  it("cancels a registration", async () => {
    const domains = fakeDomains();
    const user = show(domains);

    await user.click(await screen.findByRole("button", { name: "Register a domain" }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Cancel" }),
    );

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(domains.register).not.toHaveBeenCalled();
  });
});
