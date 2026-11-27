# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing texts of the local pages."""

from gandi_mcp.i18n.message import N_

TITLE_TOKEN = N_("Personal Access Token - gandi-mcp")
TITLE_CONFIRMATION = N_("Confirmation - gandi-mcp")
TOKEN_INTRO_PRODUCTION = N_("Enter the Personal Access Token of the production account {account}.")
TOKEN_INTRO_SANDBOX = N_("Enter the Personal Access Token of the sandbox account {account}.")
TOKEN_LABEL = N_("Personal Access Token")
TOKEN_HELP = N_("Create a token in the Gandi administration")
SAVE = N_("Save")
CONFIRM = N_("Confirm")
REFUSE = N_("Refuse")
SAVED = N_("The account {account} is saved for the Gandi user {username}. You can close this page.")
INVALID_TOKEN = N_(
    "This is not a valid Personal Access Token: copy it again from the Gandi administration."
)
TOKEN_REJECTED = N_(
    "Gandi refused this token for this environment. Nothing was saved: ask the assistant "
    "to open a new page, then enter a valid token."
)
DUPLICATE_ACCOUNT = N_("An account is already named {account}. Nothing was saved.")
ACCOUNT_GONE = N_("The account {account} no longer exists. Nothing was saved.")
ACCOUNT_CHANGED = N_(
    "The account {account} was replaced or moved to another environment while this "
    "page was open. Nothing was saved: ask the assistant to open a new page."
)
GANDI_UNAVAILABLE = N_("Gandi cannot be reached right now. Nothing was saved: try again later.")
KEYRING_UNAVAILABLE = N_(
    "The keyring of the system is unavailable. Nothing was saved: unlock or install it, "
    "then try again."
)
PREFERENCES_UNAVAILABLE = N_(
    "The preferences of gandi-mcp cannot be saved. Nothing was saved: check the preferences "
    "file, then try again."
)
CONFIRMED = N_(
    "Operation confirmed. Go back to the conversation and ask the assistant to continue."
)
REFUSED = N_("Operation refused. Nothing was changed.")
SECRET_REQUIRED = N_(
    "Enter the value asked for (at most {max_length} characters, no control character) "
    "to confirm, or refuse the operation."
)
PAGE_EXPIRED = N_("This page has expired or was already used. Nothing was changed.")
REQUEST_REFUSED = N_("This request was refused. Nothing was changed.")
