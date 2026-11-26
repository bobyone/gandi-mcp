# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""User-facing messages of the confirmation notion."""

from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_request import ConfirmationRequest
from gandi_mcp.i18n.message import N_
from gandi_mcp.i18n.translator import Translator

CONFIRM_IN_PRODUCTION = N_("Confirm on the production account {account}: {action}")
CONFIRM_IN_SANDBOX = N_("Confirm on the sandbox account {account}: {action}")
OPEN_CONFIRMATION_PAGE = N_("Open this page to confirm or refuse the operation.")


def confirmation_prompt(
    translator: Translator, request: ConfirmationRequest, locale: str | None
) -> str:
    """Render the question asked to the user, naming the account and its environment."""
    action = translator.translate(request.description.message, locale, **request.description.params)
    prompt = (
        CONFIRM_IN_PRODUCTION
        if request.environment is Environment.PRODUCTION
        else CONFIRM_IN_SANDBOX
    )
    return translator.translate(prompt, locale, account=str(request.account), action=action)
