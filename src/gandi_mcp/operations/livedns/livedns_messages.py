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

# Destructive zone changes: the counts come from a read before the confirmation.
REPLACE_ZONE = N_(
    "replace all the records of the zone of {domain} (now: {count}, after the change: "
    "{new}); its NS records at @ are kept"
)
REPLACE_ZONE_WITHOUT_APEX_NS = N_(
    "replace all the records of the zone of {domain} (now: {count}, after the change: "
    "{new}); its NS records at @ are removed too"
)
IMPORT_ZONE = N_(
    "replace all the records of the zone of {domain} with the zone file {file} (now: "
    "{count}, after the change: {new})"
)
DELETE_ZONE = N_("delete all the records of the zone of {domain} (now: {count})")
RESTORE_SNAPSHOT = N_(
    "replace all the records of the zone of {domain} with the snapshot {snapshot} (now: "
    "{count}, after the change: {new})"
)
REPLACE_NAME_RECORDS = N_(
    "replace the records of {name} in the zone of {domain} (now: {count}, after the change: {new})"
)
DELETE_NAME_RECORDS = N_("delete the records of {name} in the zone of {domain} (now: {count})")
REPLACE_RECORD = N_(
    "replace the values of the {type} record of {name} in the zone of {domain} (now: "
    "{count}, after the change: {new})"
)
REMOVE_RECORD_VALUES = N_(
    "remove values of the {type} record of {name} in the zone of {domain} (removed: "
    "{count}, left: {left}; with none left, the record is deleted)"
)
DELETE_RECORD = N_("delete the {type} record of {name} in the zone of {domain} (values: {count})")
SNAPSHOT_FIRST = N_("Create a snapshot of the zone first (automatic snapshots are off)")
SNAPSHOT_FIRST_AUTOMATIC = N_(
    "Create a snapshot of the zone first (automatic snapshots are on: LiveDNS also saves "
    "the zone after each change)"
)
