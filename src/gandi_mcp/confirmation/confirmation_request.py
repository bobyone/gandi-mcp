# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Value object of a confirmation asked to the user."""

from dataclasses import dataclass

from gandi_mcp.accounts.account_name import AccountName
from gandi_mcp.accounts.environment import Environment
from gandi_mcp.confirmation.confirmation_option import ConfirmationOption
from gandi_mcp.confirmation.secret_input import SecretInput
from gandi_mcp.i18n.localized_text import LocalizedText
from gandi_mcp.operations.operation_category import OperationCategory


@dataclass(frozen=True)
class ConfirmationRequest:
    """What the user is asked to confirm.

    Attributes:
        subject: Fingerprint of the exact operation and its parameters; a given
            confirmation is only valid for the same subject.
        category: Destructive or billable.
        description: Readable description of the operation.
        account: Account the operation acts on.
        environment: Environment of that account.
        secret_input: A secret the user must type to confirm (ADR 11), if any; only
            channels collecting secrets outside the model can ask for it.
        option: A yes or no choice offered with the confirmation (ADR 14), if any.
    """

    subject: str
    category: OperationCategory
    description: LocalizedText
    account: AccountName
    environment: Environment
    secret_input: SecretInput | None = None
    option: ConfirmationOption | None = None
