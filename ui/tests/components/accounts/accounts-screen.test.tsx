// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { AccountsError, type Account } from "../../../src/api/account";
import type { AccountsApi } from "../../../src/api/accounts-api";
import { AccountsScreen } from "../../../src/components/accounts/accounts-screen";
import { createI18n } from "../../../src/i18n/i18n";

const TOKEN = "pat_0123456789abcdef";
const PERSO: Account = {
  name: "Perso",
  environment: "sandbox",
  readOnly: false,
  isDefault: true,
  removalPending: false,
  payingOrganization: null,
};
const PRO: Account = {
  name: "Pro",
  environment: "production",
  readOnly: true,
  isDefault: false,
  removalPending: false,
  payingOrganization: null,
};

let i18n: I18n;

beforeAll(async () => {
  i18n = await createI18n("en");
});

function fakeApi(accounts: Account[] = [PERSO, PRO]) {
  return {
    list: vi.fn<AccountsApi["list"]>().mockResolvedValue(accounts),
    add: vi.fn<AccountsApi["add"]>().mockResolvedValue({ account: PERSO, username: "ada" }),
    update: vi.fn<AccountsApi["update"]>().mockResolvedValue(PRO),
    replaceToken: vi
      .fn<AccountsApi["replaceToken"]>()
      .mockResolvedValue({ account: PERSO, username: "ada" }),
    changeEnvironment: vi
      .fn<AccountsApi["changeEnvironment"]>()
      .mockResolvedValue({ account: PERSO, username: "ada" }),
    remove: vi.fn<AccountsApi["remove"]>().mockResolvedValue(null),
    organizations: vi
      .fn<AccountsApi["organizations"]>()
      .mockResolvedValue([{ id: "org-1", name: "Ada SARL", type: "company" }]),
    setPayingOrganization: vi
      .fn<AccountsApi["setPayingOrganization"]>()
      .mockResolvedValue({ ...PERSO, payingOrganization: "org-1" }),
  } satisfies AccountsApi;
}

function show(api: AccountsApi) {
  render(
    <I18nextProvider i18n={i18n}>
      <AccountsScreen api={api} />
    </I18nextProvider>,
  );
  return userEvent.setup();
}

/** Open the action menu of an account and return it. */
async function openActions(user: ReturnType<typeof userEvent.setup>, name: string) {
  const toggle = await screen.findByRole("button", { name: `Actions for ${name}` });
  await user.click(toggle);
  return within(toggle.parentElement!);
}

describe("AccountsScreen", () => {
  it("lists the accounts with their environment and status", async () => {
    show(fakeApi());

    const rows = await screen.findAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(within(rows[1]!).getByText("Default account")).toBeInTheDocument();
    expect(within(rows[2]!).getByText("Production")).toBeInTheDocument();
    expect(within(rows[2]!).getByText("Read-only")).toBeInTheDocument();
    expect(screen.getByText("2 accounts")).toBeInTheDocument();
  });

  it("marks an account whose removal is not finished", async () => {
    show(fakeApi([{ ...PRO, removalPending: true }]));

    expect(await screen.findByText("Removal not finished")).toBeInTheDocument();
  });

  it("shows the loading state and the empty state", async () => {
    show(fakeApi([]));

    expect(screen.getByRole("status")).toHaveTextContent("Loading the accounts");
    expect(await screen.findByText(/No Gandi account yet/)).toBeInTheDocument();
  });

  it("explains a failure to list", async () => {
    const api = fakeApi();
    api.list.mockRejectedValue(new AccountsError("The keyring is unavailable."));
    show(api);

    expect(await screen.findByRole("alert")).toHaveTextContent("The keyring is unavailable.");
  });

  it("adds an account after validating the form", async () => {
    const api = fakeApi([]);
    const user = show(api);

    await user.click(await screen.findByRole("button", { name: "Add account" }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: "Save" }));
    expect(within(dialog).getByText(/Use 1 to 40 letters/)).toBeVisible();
    expect(api.add).not.toHaveBeenCalled();
    await user.type(within(dialog).getByLabelText("Account name"), "  Perso ");
    await user.selectOptions(within(dialog).getByLabelText("Environment"), "production");
    await user.click(within(dialog).getByLabelText("Read-only account"));
    await user.type(within(dialog).getByLabelText("Personal Access Token"), TOKEN);
    expect(within(dialog).getByRole("link")).toHaveAttribute("href", "https://admin.gandi.net/");
    await user.click(within(dialog).getByRole("button", { name: "Save" }));

    expect(api.add).toHaveBeenCalledWith(
      { name: "Perso", environment: "production", readOnly: true, token: TOKEN },
      TOKEN,
    );
    expect(
      await screen.findByText("The account Perso is saved for the Gandi user ada."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(api.list).toHaveBeenCalledTimes(2);
  });

  it("shows the server explanation when adding fails", async () => {
    const api = fakeApi([]);
    api.add.mockRejectedValue(new AccountsError("Gandi refused the token."));
    const user = show(api);

    await user.click(await screen.findByRole("button", { name: "Add account" }));
    const dialog = await screen.findByRole("dialog");
    await user.type(within(dialog).getByLabelText("Account name"), "Perso");
    await user.type(within(dialog).getByLabelText("Personal Access Token"), TOKEN);
    await user.click(within(dialog).getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Gandi refused the token.");
  });

  it("falls back to a generic message", async () => {
    const api = fakeApi();
    api.update.mockRejectedValue(new Error("internal"));
    const user = show(api);

    await user.click(
      (await openActions(user, "Pro")).getByRole("button", { name: "Set as default" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("The operation failed");
    await user.click(screen.getByRole("button", { name: "Close" }));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("cancels a dialog without calling the server", async () => {
    const api = fakeApi();
    const user = show(api);

    await user.click(await screen.findByRole("button", { name: "Add account" }));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(api.add).not.toHaveBeenCalled();
  });

  it("renames an account", async () => {
    const api = fakeApi();
    const user = show(api);

    await user.click((await openActions(user, "Perso")).getByRole("button", { name: "Rename" }));
    const input = within(await screen.findByRole("dialog")).getByLabelText("Account name");
    await user.clear(input);
    await user.click(screen.getByRole("button", { name: "Save" }));
    expect(api.update).not.toHaveBeenCalled();
    await user.type(input, "Home");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(api.update).toHaveBeenCalledWith("Perso", { newName: "Home" }, undefined);
    expect(await screen.findByText("The account Pro is updated.")).toBeInTheDocument();
  });

  it("replaces a token and changes the environment", async () => {
    const api = fakeApi();
    const user = show(api);

    await user.click(
      (await openActions(user, "Perso")).getByRole("button", { name: "Replace token" }),
    );
    let dialog = await screen.findByRole("dialog");
    expect(within(dialog).queryByLabelText("Environment")).not.toBeInTheDocument();
    await user.type(within(dialog).getByLabelText("Personal Access Token"), TOKEN);
    await user.click(within(dialog).getByRole("button", { name: "Save" }));
    expect(api.replaceToken).toHaveBeenCalledWith("Perso", TOKEN);

    await user.click(
      (await openActions(user, "Pro")).getByRole("button", { name: "Change environment" }),
    );
    dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByLabelText("Environment")).toHaveValue("sandbox");
    await user.type(within(dialog).getByLabelText("Personal Access Token"), TOKEN);
    await user.click(within(dialog).getByRole("button", { name: "Save" }));
    expect(api.changeEnvironment).toHaveBeenCalledWith("Pro", "sandbox", TOKEN);
  });

  it("moves a sandbox account to production by default", async () => {
    const user = show(fakeApi());

    await user.click(
      (await openActions(user, "Perso")).getByRole("button", { name: "Change environment" }),
    );

    expect(within(await screen.findByRole("dialog")).getByLabelText("Environment")).toHaveValue(
      "production",
    );
  });

  it("makes an account read-only and asks before allowing writes", async () => {
    const api = fakeApi();
    const user = show(api);

    await user.click(
      (await openActions(user, "Perso")).getByRole("button", { name: "Make read-only" }),
    );
    expect(api.update).toHaveBeenCalledWith("Perso", { readOnly: true }, undefined);

    await user.click(
      (await openActions(user, "Pro")).getByRole("button", { name: "Allow writes" }),
    );
    const dialog = await screen.findByRole("dialog", { name: "Allow writes on Pro?" });
    await user.click(within(dialog).getByRole("button", { name: "Allow writes" }));
    expect(api.update).toHaveBeenCalledWith("Pro", { readOnly: false }, undefined);
  });

  it("asks before removing an account", async () => {
    const api = fakeApi();
    const user = show(api);

    await user.click((await openActions(user, "Pro")).getByRole("button", { name: "Remove" }));
    const dialog = await screen.findByRole("dialog", { name: "Remove the account Pro?" });
    expect(dialog).toHaveTextContent("Nothing changes at Gandi.");
    await user.click(within(dialog).getByRole("button", { name: "Remove" }));

    expect(api.remove).toHaveBeenCalledWith("Pro", undefined);
    expect(await screen.findByText("The account Pro is removed.")).toBeInTheDocument();
  });

  it("keeps the account when its token cannot be removed", async () => {
    const api = fakeApi();
    api.remove.mockRejectedValue(new AccountsError("The keyring of the system is unavailable."));
    const user = show(api);

    await user.click((await openActions(user, "Pro")).getByRole("button", { name: "Remove" }));
    const dialog = await screen.findByRole("dialog", { name: "Remove the account Pro?" });
    await user.click(within(dialog).getByRole("button", { name: "Remove" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("keyring of the system");
    expect(screen.getByRole("button", { name: "Actions for Pro" })).toBeInTheDocument();
  });

  it("waits for the confirmation asked outside the App before removing", async () => {
    const api = fakeApi();
    api.remove.mockResolvedValueOnce({ confirmationId: "c-1" });
    const user = show(api);

    await user.click((await openActions(user, "Pro")).getByRole("button", { name: "Remove" }));
    const dialog = await screen.findByRole("dialog", { name: "Remove the account Pro?" });
    await user.click(within(dialog).getByRole("button", { name: "Remove" }));

    expect(await screen.findByText(/in the window opened by gandi-mcp/)).toBeInTheDocument();
    expect(screen.queryByText("The account Pro is removed.")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(api.remove).toHaveBeenLastCalledWith("Pro", "c-1");
    expect(await screen.findByText("The account Pro is removed.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Continue" })).not.toBeInTheDocument();
  });

  it("waits for the confirmation before allowing writes", async () => {
    const api = fakeApi();
    api.update.mockResolvedValueOnce({ confirmationId: "c-2" });
    const user = show(api);

    await user.click(
      (await openActions(user, "Pro")).getByRole("button", { name: "Allow writes" }),
    );
    const dialog = await screen.findByRole("dialog", { name: "Allow writes on Pro?" });
    await user.click(within(dialog).getByRole("button", { name: "Allow writes" }));
    await user.click(await screen.findByRole("button", { name: "Continue" }));

    expect(api.update).toHaveBeenLastCalledWith("Pro", { readOnly: false }, "c-2");
    expect(await screen.findByText("The account Pro is updated.")).toBeInTheDocument();
  });

  it("offers no set-as-default action for the default account", async () => {
    const user = show(fakeApi());

    const menu = await openActions(user, "Perso");

    expect(menu.queryByRole("button", { name: "Set as default" })).not.toBeInTheDocument();
  });

  it("chooses the paying organization among those of the account", async () => {
    const api = fakeApi();
    const user = show(api);

    await (await openActions(user, "Perso")).findByText("Choose the paying organization");
    await user.click(screen.getByText("Choose the paying organization"));
    const dialog = await screen.findByRole("dialog");
    await user.selectOptions(await within(dialog).findByLabelText("Paying organization"), "org-1");
    await user.click(within(dialog).getByRole("button", { name: "Save" }));

    expect(api.organizations).toHaveBeenCalledWith("Perso");
    expect(api.setPayingOrganization).toHaveBeenCalledWith("Perso", "org-1");
    expect(await screen.findByText("The account Perso is updated.")).toBeInTheDocument();
  });

  it("clears the paying organization", async () => {
    const api = fakeApi([{ ...PERSO, payingOrganization: "org-1" }]);
    const user = show(api);

    await openActions(user, "Perso");
    await user.click(screen.getByText("Choose the paying organization"));
    const dialog = await screen.findByRole("dialog");
    const select = await within(dialog).findByLabelText("Paying organization");
    expect(select).toHaveValue("org-1");
    await user.selectOptions(select, "");
    await user.click(within(dialog).getByRole("button", { name: "Save" }));

    expect(api.setPayingOrganization).toHaveBeenCalledWith("Perso", null);
  });

  it("explains why the organizations cannot be listed", async () => {
    const api = fakeApi();
    api.organizations.mockRejectedValueOnce(new AccountsError("Gandi is unavailable."));
    api.organizations.mockRejectedValueOnce(new Error("odd"));
    const user = show(api);

    await openActions(user, "Perso");
    await user.click(screen.getByText("Choose the paying organization"));
    expect(await within(await screen.findByRole("dialog")).findByRole("alert")).toHaveTextContent(
      "Gandi is unavailable.",
    );
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await openActions(user, "Perso");
    await user.click(screen.getByText("Choose the paying organization"));
    expect(await within(await screen.findByRole("dialog")).findByRole("alert")).toHaveTextContent(
      "The operation failed",
    );
  });
});
