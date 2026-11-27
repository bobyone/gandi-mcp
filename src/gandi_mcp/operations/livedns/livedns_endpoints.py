# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Catalogue of the Gandi LiveDNS API endpoints (https://api.gandi.net/docs/livedns/)."""

from gandi_mcp.gandi.media_type import MediaType
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.livedns import livedns_messages as messages
from gandi_mcp.operations.operation_category import OperationCategory

READ = OperationCategory.READ
WRITE = OperationCategory.WRITE
DESTRUCTIVE = OperationCategory.DESTRUCTIVE
# Gandi answers 200 to a creation that already exists with the same values.
UNCHANGED = 200
DOMAIN = ("livedns", "domains", "{domain}")
RECORDS = (*DOMAIN, "records")
SNAPSHOT = (*DOMAIN, "snapshots", "{snapshot}")
TSIG_KEY = ("livedns", "axfr", "tsig", "{key}")
PAGE = frozenset({"page", "per_page"})
SHARING = frozenset({"sharing_id"})

RECORD_TYPES = Endpoint("livedns_record_types", "GET", ("livedns", "dns", "rrtypes"), READ)
DOMAINS = Endpoint("livedns_domains", "GET", ("livedns", "domains"), READ, PAGE | SHARING)
DOMAIN_DETAILS = Endpoint("livedns_domain", "GET", DOMAIN, READ)
NAMESERVERS = Endpoint("livedns_nameservers", "GET", (*DOMAIN, "nameservers"), READ)
# Generic route hashing any name. Gandi documents it without authentication, but
# answers 401 without a token (production and sandbox, 2026-11-28).
PUBLIC_NAMESERVERS = Endpoint(
    "livedns_public_nameservers", "GET", ("livedns", "nameservers", "{domain}"), READ
)
RECORD_LIST = Endpoint("livedns_records", "GET", RECORDS, READ, PAGE | {"rrset_type", "sort_by"})
NAME_RECORDS = Endpoint("livedns_name_records", "GET", (*RECORDS, "{name}"), READ)
RECORD = Endpoint("livedns_record", "GET", (*RECORDS, "{name}", "{type}"), READ)
# The whole zone as a zone file, written to the work directory.
ZONE_EXPORT = Endpoint("livedns_zone_export", "GET", RECORDS, READ, accept=MediaType.TEXT)
SNAPSHOTS = Endpoint(
    "livedns_snapshots",
    "GET",
    (*DOMAIN, "snapshots"),
    READ,
    PAGE | {"automatic", "sort_by"},
)
SNAPSHOT_DETAILS = Endpoint("livedns_snapshot", "GET", SNAPSHOT, READ)
SNAPSHOT_EXPORT = Endpoint("livedns_snapshot_export", "GET", SNAPSHOT, READ, accept=MediaType.TEXT)
SIGNING_KEYS = Endpoint("livedns_signing_keys", "GET", (*DOMAIN, "keys"), READ)
SIGNING_KEY = Endpoint("livedns_signing_key", "GET", (*DOMAIN, "keys", "{key}"), READ)
SECONDARY_SERVERS = Endpoint("livedns_secondary_servers", "GET", (*DOMAIN, "axfr", "slaves"), READ)
TSIG_KEYS = Endpoint("livedns_tsig_keys", "GET", ("livedns", "axfr", "tsig"), READ, SHARING)
TSIG_KEY_DETAILS = Endpoint("livedns_tsig_key", "GET", TSIG_KEY, READ, SHARING)
# The sample holds the secret of the key: always read with the key (TsigConfiguration).
TSIG_CONFIG = Endpoint(
    "livedns_tsig_config", "GET", (*TSIG_KEY, "config", "{software}"), READ, SHARING
)
DOMAIN_TSIG_KEYS = Endpoint("livedns_domain_tsig_keys", "GET", (*DOMAIN, "axfr", "tsig"), READ)
RECORD_PATH = (*RECORDS, "{name}", "{type}")
DOMAIN_TSIG_KEY = (*DOMAIN, "axfr", "tsig", "{key}")

DOMAIN_ADD = Endpoint("livedns_domain_add", "POST", ("livedns", "domains"), WRITE, SHARING)
AUTOMATIC_SNAPSHOTS_UPDATE = Endpoint("livedns_automatic_snapshots_update", "PATCH", DOMAIN, WRITE)
# Gandi also creates a record through the zone or the name path, with the same effect:
# one tool covers the three (ADR 13).
RECORD_CREATE = Endpoint(
    "livedns_record_create", "POST", RECORD_PATH, WRITE, unchanged_status=UNCHANGED
)
RECORD_VALUES_ADD = Endpoint("livedns_record_values_add", "PATCH", RECORD_PATH, WRITE)
DOMAIN_VERIFICATION = Endpoint(
    "livedns_domain_verification", "POST", (*DOMAIN, "verification", "{name}", "{type}"), WRITE
)
SNAPSHOT_CREATE = Endpoint("livedns_snapshot_create", "POST", (*DOMAIN, "snapshots"), WRITE)
SNAPSHOT_RENAME = Endpoint("livedns_snapshot_rename", "PATCH", SNAPSHOT, WRITE)
SNAPSHOT_DELETE = Endpoint(
    "livedns_snapshot_delete", "DELETE", SNAPSHOT, DESTRUCTIVE, description=messages.DELETE_SNAPSHOT
)
SIGNING_KEY_CREATE = Endpoint("livedns_signing_key_create", "POST", (*DOMAIN, "keys"), WRITE)
SIGNING_KEY_RESTORE = Endpoint(
    "livedns_signing_key_restore", "PATCH", (*DOMAIN, "keys", "{key}"), WRITE
)
SIGNING_KEY_DELETE = Endpoint(
    "livedns_signing_key_delete",
    "DELETE",
    (*DOMAIN, "keys", "{key}"),
    DESTRUCTIVE,
    description=messages.DELETE_SIGNING_KEY,
)
SECONDARY_SERVER_ADD = Endpoint(
    "livedns_secondary_server_add", "PUT", (*DOMAIN, "axfr", "slaves", "{ip}"), WRITE
)
SECONDARY_SERVER_REMOVE = Endpoint(
    "livedns_secondary_server_remove",
    "DELETE",
    (*DOMAIN, "axfr", "slaves", "{ip}"),
    DESTRUCTIVE,
    description=messages.REMOVE_SECONDARY_SERVER,
)
TSIG_KEY_CREATE = Endpoint(
    "livedns_tsig_key_create", "POST", ("livedns", "axfr", "tsig"), WRITE, SHARING
)
DOMAIN_TSIG_KEY_ADD = Endpoint(
    "livedns_domain_tsig_key_add", "PUT", DOMAIN_TSIG_KEY, WRITE, SHARING
)
DOMAIN_TSIG_KEY_REMOVE = Endpoint(
    "livedns_domain_tsig_key_remove",
    "DELETE",
    DOMAIN_TSIG_KEY,
    DESTRUCTIVE,
    SHARING,
    description=messages.REMOVE_DOMAIN_TSIG_KEY,
)

READ_ENDPOINTS: tuple[Endpoint, ...] = (
    RECORD_TYPES,
    DOMAINS,
    DOMAIN_DETAILS,
    NAMESERVERS,
    PUBLIC_NAMESERVERS,
    RECORD_LIST,
    NAME_RECORDS,
    RECORD,
    ZONE_EXPORT,
    SNAPSHOTS,
    SNAPSHOT_DETAILS,
    SNAPSHOT_EXPORT,
    SIGNING_KEYS,
    SIGNING_KEY,
    SECONDARY_SERVERS,
    TSIG_KEYS,
    TSIG_KEY_DETAILS,
    TSIG_CONFIG,
    DOMAIN_TSIG_KEYS,
)

WRITE_ENDPOINTS: tuple[Endpoint, ...] = (
    DOMAIN_ADD,
    AUTOMATIC_SNAPSHOTS_UPDATE,
    RECORD_CREATE,
    RECORD_VALUES_ADD,
    DOMAIN_VERIFICATION,
    SNAPSHOT_CREATE,
    SNAPSHOT_RENAME,
    SNAPSHOT_DELETE,
    SIGNING_KEY_CREATE,
    SIGNING_KEY_RESTORE,
    SIGNING_KEY_DELETE,
    SECONDARY_SERVER_ADD,
    SECONDARY_SERVER_REMOVE,
    TSIG_KEY_CREATE,
    DOMAIN_TSIG_KEY_ADD,
    DOMAIN_TSIG_KEY_REMOVE,
)
