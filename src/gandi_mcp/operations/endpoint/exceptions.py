# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Exceptions of the endpoint notion."""


class EndpointError(Exception):
    """Base class of the endpoint errors."""


class InvalidEndpointArgumentsError(EndpointError):
    """The arguments of an endpoint call do not match its specification."""
