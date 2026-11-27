// SPDX-FileCopyrightText: 2026 bobyone
// SPDX-License-Identifier: GPL-2.0-or-later
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { i18n as I18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import { beforeAll, describe, expect, it, vi } from "vitest";
import { DomainsError, type Quote } from "../../../src/api/domain";
import type { DomainsApi } from "../../../src/api/domains-api";
import { RegisterDialog } from "../../../src/components/domains/register-dialog";
import { createI18n } from "../../../src/i18n/i18n";

const QUOTE: Quote = {
  status: "available",
  currency: "EUR",
  bands: [
    { minYears: 1, maxYears: 1, perYearAfterTaxes: 12 },
    { minYears: 2, maxYears: 5, perYearAfterTaxes: 10 },
  ],
};

let i18n: I18n;

beforeAll(async () => {
  i18n = await createI18n("en");
});

function fakeApi() {
  return {
    list: vi.fn<DomainsApi["list"]>(),
    details: vi.fn<DomainsApi["details"]>(),
    quote: vi.fn<DomainsApi["quote"]>().mockResolvedValue(QUOTE),
    setAutorenew: vi.fn<DomainsApi["setAutorenew"]>(),
    setTransferLock: vi.fn<DomainsApi["setTransferLock"]>(),
    setNameservers: vi.fn<DomainsApi["setNameservers"]>(),
    renew: vi.fn<DomainsApi["renew"]>(),
    register: vi.fn<DomainsApi["register"]>(),
  } satisfies DomainsApi;
}

function show(api: DomainsApi) {
  const onSubmit = vi.fn();
  const onCancel = vi.fn();
  render(
    <I18nextProvider i18n={i18n}>
      <RegisterDialog
        api={api}
        account="Perso"
        busy={false}
        onSubmit={onSubmit}
        onCancel={onCancel}
      />
    </I18nextProvider>,
  );
  return {
    user: userEvent.setup(),
    onSubmit,
    onCancel,
    dialog: within(screen.getByRole("dialog")),
  };
}

describe("RegisterDialog", () => {
  it("checks the name before asking Gandi", async () => {
    const api = fakeApi();
    const { user, dialog } = show(api);

    expect(dialog.getByRole("button", { name: "Register a domain" })).toBeDisabled();
    await user.type(dialog.getByLabelText("Domain"), "nodot{enter}");

    expect(dialog.getByText(/Enter a domain name/)).toBeVisible();
    expect(api.quote).not.toHaveBeenCalled();
  });

  it("registers an available name with its owner", async () => {
    const api = fakeApi();
    const { user, dialog, onSubmit } = show(api);

    await user.type(dialog.getByLabelText("Domain"), " new.fr ");
    await user.click(dialog.getByRole("button", { name: "Check availability" }));
    expect(await dialog.findByText("new.fr is available.")).toBeInTheDocument();
    expect(dialog.getByText("€12.00 per year, taxes included")).toBeInTheDocument();
    await user.selectOptions(dialog.getByLabelText("Duration"), "2");
    expect(dialog.getByText("€10.00 per year, taxes included")).toBeInTheDocument();

    await user.click(dialog.getByRole("button", { name: "Register a domain" }));
    expect(dialog.getAllByText("Fill in this field.")[0]).toBeVisible();
    expect(onSubmit).not.toHaveBeenCalled();

    expect(dialog.queryByLabelText("Organization name")).not.toBeInTheDocument();
    await user.selectOptions(dialog.getByLabelText("Kind of contact"), "company");
    await user.type(dialog.getByLabelText("Organization name"), "Ada SARL");
    await user.type(dialog.getByLabelText("First name"), "Ada");
    await user.type(dialog.getByLabelText("Last name"), "Lovelace");
    await user.type(dialog.getByLabelText("Email address"), "ada@example.com");
    await user.type(dialog.getByLabelText("Phone"), "0123");
    await user.type(dialog.getByLabelText("Street address"), "1 rue de la Paix");
    await user.type(dialog.getByLabelText("Postal code"), "75002");
    await user.type(dialog.getByLabelText("City"), "Paris");
    await user.type(dialog.getByLabelText("Country"), "FR");
    await user.click(dialog.getByRole("button", { name: "Register a domain" }));
    expect(dialog.getByText(/Write the phone as/)).toBeVisible();
    await user.clear(dialog.getByLabelText("Phone"));
    await user.click(dialog.getByRole("button", { name: "Register a domain" }));

    expect(api.quote).toHaveBeenCalledWith("Perso", "new.fr", "create");
    expect(onSubmit).toHaveBeenCalledWith(
      "new.fr",
      2,
      expect.objectContaining({ type: "company", orgname: "Ada SARL", country: "FR" }),
    );
  });

  it("says when a name cannot be registered and asks again after a change", async () => {
    const api = fakeApi();
    api.quote.mockResolvedValueOnce({ ...QUOTE, status: "unavailable" });
    const { user, dialog } = show(api);

    await user.type(dialog.getByLabelText("Domain"), "taken.com");
    await user.click(dialog.getByRole("button", { name: "Check availability" }));
    expect(await dialog.findByText("taken.com cannot be registered.")).toBeInTheDocument();
    expect(dialog.queryByLabelText("Duration")).not.toBeInTheDocument();

    await user.type(dialog.getByLabelText("Domain"), "{backspace}{backspace}{backspace}fr");
    expect(dialog.queryByText(/cannot be registered/)).not.toBeInTheDocument();
    await user.type(dialog.getByLabelText("Domain"), "{enter}");
    expect(await dialog.findByText("taken.fr is available.")).toBeInTheDocument();
  });

  it("explains a failed check", async () => {
    const api = fakeApi();
    api.quote.mockRejectedValueOnce(new DomainsError("Unknown extension."));
    api.quote.mockRejectedValueOnce("odd");
    const { user, dialog, onCancel } = show(api);

    await user.type(dialog.getByLabelText("Domain"), "a.zz");
    await user.click(dialog.getByRole("button", { name: "Check availability" }));
    expect(await dialog.findByText("Unknown extension.")).toBeInTheDocument();
    await user.click(dialog.getByRole("button", { name: "Check availability" }));
    expect(await dialog.findByText("The operation failed")).toBeInTheDocument();
    await user.click(dialog.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalled();
  });
});
