# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Descriptions of the orders, shown in their confirmation with their price."""

from gandi_mcp.i18n.message import N_, ngettext

REGISTER = ngettext(
    "register {domain} for {count} year: {price} including taxes",
    "register {domain} for {count} years: {price} including taxes",
)
RENEW = ngettext(
    "renew {domain} for {count} year: {price} including taxes",
    "renew {domain} for {count} years: {price} including taxes",
)
RESTORE = N_("restore {domain}: {price} including taxes")
TRANSFER_IN = ngettext(
    "transfer {domain} to Gandi, with {count} year of renewal: {price} including taxes",
    "transfer {domain} to Gandi, with {count} years of renewal: {price} including taxes",
)
AUTHORIZATION_CODE = N_("Authorization code given by the current registrar")
