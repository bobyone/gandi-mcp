# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Descriptions of the confirmed LiveDNS operations, shown in their confirmation."""

from gandi_mcp.i18n.message import N_

DELETE_SNAPSHOT = N_("delete the snapshot {snapshot} of the zone of {domain}")
DELETE_SIGNING_KEY = N_(
    "delete the signing key {key} of the zone of {domain}: if its DS record is still "
    "published at the registry, the domain may stop resolving"
)
REMOVE_SECONDARY_SERVER = N_("stop allowing {ip} to transfer the zone of {domain}")
REMOVE_DOMAIN_TSIG_KEY = N_("dissociate the TSIG key {key} from the zone of {domain}")
