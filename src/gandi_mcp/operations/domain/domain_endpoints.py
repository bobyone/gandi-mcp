# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Catalogue of the Gandi Domain API endpoints (https://api.gandi.net/docs/domains/)."""

from gandi_mcp.operations.domain import domain_messages as messages
from gandi_mcp.operations.domain.billable.messages import AUTHORIZATION_CODE
from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.operations.operation_category import OperationCategory

READ = OperationCategory.READ
WRITE = OperationCategory.WRITE
DESTRUCTIVE = OperationCategory.DESTRUCTIVE
DOMAIN = ("domain", "domains", "{domain}")
PAGE = frozenset({"page", "per_page"})

CHECK_AVAILABILITY = DomainEndpoint(
    "domain_check_availability",
    "GET",
    ("domain", "check"),
    READ,
    frozenset({"name", "processes", "currency", "country", "lang", "sharing_id", "max_duration"}),
)
LIST_TLDS = DomainEndpoint("domain_list_tlds", "GET", ("domain", "tlds"), READ, PAGE | {"category"})
TLD_DETAILS = DomainEndpoint("domain_tld_details", "GET", ("domain", "tlds", "{tld}"), READ)
LIST_DOMAINS = DomainEndpoint(
    "domain_list",
    "GET",
    ("domain", "domains"),
    READ,
    PAGE | {"fqdn", "tld", "nameserver", "sort_by", "sharing_id"},
)
DETAILS = DomainEndpoint("domain_details", "GET", DOMAIN, READ)
CREATION_STATUS = DomainEndpoint(
    "domain_creation_status",
    "GET",
    (*DOMAIN, "createstatus"),
    READ,
    completes_with_see_other=True,
)
CONTACTS = DomainEndpoint("domain_contacts", "GET", (*DOMAIN, "contacts"), READ)
NAMESERVERS = DomainEndpoint("domain_nameservers", "GET", (*DOMAIN, "nameservers"), READ)
LIVEDNS_STATUS = DomainEndpoint("domain_livedns_status", "GET", (*DOMAIN, "livedns"), READ)
DNSSEC_STATUS = DomainEndpoint("domain_dnssec_status", "GET", (*DOMAIN, "livedns", "dnssec"), READ)
DNSSEC_KEYS = DomainEndpoint("domain_dnssec_keys", "GET", (*DOMAIN, "dnskeys"), READ, PAGE)
GLUE_RECORDS = DomainEndpoint("domain_glue_records", "GET", (*DOMAIN, "hosts"), READ, PAGE)
GLUE_RECORD = DomainEndpoint("domain_glue_record", "GET", (*DOMAIN, "hosts", "{host}"), READ)
WEB_REDIRECTIONS = DomainEndpoint(
    "domain_web_redirections", "GET", (*DOMAIN, "webredirs"), READ, PAGE
)
WEB_REDIRECTION = DomainEndpoint(
    "domain_web_redirection", "GET", (*DOMAIN, "webredirs", "{host}"), READ
)
TAGS = DomainEndpoint("domain_tags", "GET", (*DOMAIN, "tags"), READ)
RENEWAL_INFO = DomainEndpoint("domain_renewal_info", "GET", (*DOMAIN, "renew"), READ)
RESTORE_INFO = DomainEndpoint("domain_restore_info", "GET", (*DOMAIN, "restore"), READ)
CLAIMS = DomainEndpoint("domain_claims", "GET", (*DOMAIN, "claims"), READ)
OWNER_CHANGE_STATUS = DomainEndpoint(
    "domain_owner_change_status",
    "GET",
    ("domain", "changeowner", "{domain}"),
    READ,
    frozenset({"sharing_id"}),
)
TRANSFER_IN_STATUS = DomainEndpoint(
    "domain_transfer_in_status", "GET", ("domain", "transferin", "{domain}"), READ
)
# A POST that only checks whether a transfer is possible: it changes nothing.
TRANSFER_IN_CHECK = DomainEndpoint(
    "domain_transfer_in_check",
    "POST",
    ("domain", "transferin", "{domain}", "available"),
    READ,
)

READ_ENDPOINTS: tuple[DomainEndpoint, ...] = (
    CHECK_AVAILABILITY,
    LIST_TLDS,
    TLD_DETAILS,
    LIST_DOMAINS,
    DETAILS,
    CREATION_STATUS,
    CONTACTS,
    NAMESERVERS,
    LIVEDNS_STATUS,
    DNSSEC_STATUS,
    DNSSEC_KEYS,
    GLUE_RECORDS,
    GLUE_RECORD,
    WEB_REDIRECTIONS,
    WEB_REDIRECTION,
    TAGS,
    RENEWAL_INFO,
    RESTORE_INFO,
    CLAIMS,
    OWNER_CHANGE_STATUS,
    TRANSFER_IN_STATUS,
    TRANSFER_IN_CHECK,
)


# Writes and destructive operations (orders are BillableOperation classes, ADR 7).
DELETE = DomainEndpoint(
    "domain_delete", "DELETE", DOMAIN, DESTRUCTIVE, description=messages.DELETE_DOMAIN
)
AUTORENEW = DomainEndpoint("domain_autorenew_update", "PATCH", (*DOMAIN, "autorenew"), WRITE)
TRANSFER_LOCK = DomainEndpoint("domain_transfer_lock_update", "PATCH", (*DOMAIN, "status"), WRITE)
AUTHORIZATION_CODE_RESET = DomainEndpoint(
    "domain_authorization_code_reset", "PUT", (*DOMAIN, "authinfo"), WRITE
)
REACHABILITY_RESEND = DomainEndpoint(
    "domain_reachability_resend", "PATCH", (*DOMAIN, "reachability"), WRITE
)
CLAIMS_ACCEPT = DomainEndpoint("domain_claims_accept", "POST", (*DOMAIN, "claims"), WRITE)
CONTACTS_UPDATE = DomainEndpoint("domain_contacts_update", "PATCH", (*DOMAIN, "contacts"), WRITE)
OWNER_UPDATE = DomainEndpoint(
    "domain_owner_update",
    "PUT",
    (*DOMAIN, "contacts", "owner"),
    DESTRUCTIVE,
    description=messages.UPDATE_OWNER,
    supports_dry_run=True,
)
OWNER_CHANGE = DomainEndpoint(
    "domain_owner_change",
    "POST",
    ("domain", "changeowner", "{domain}"),
    DESTRUCTIVE,
    description=messages.CHANGE_OWNER,
    supports_dry_run=True,
    follow_up="domain_owner_change_status",
)
OWNER_CHANGE_RESEND = DomainEndpoint(
    "domain_owner_change_resend", "POST", ("domain", "changeowner", "{domain}", "foa"), WRITE
)
NAMESERVERS_UPDATE = DomainEndpoint(
    "domain_nameservers_update",
    "PUT",
    (*DOMAIN, "nameservers"),
    DESTRUCTIVE,
    description=messages.UPDATE_NAMESERVERS,
)
LIVEDNS_ENABLE = DomainEndpoint(
    "domain_livedns_enable",
    "POST",
    (*DOMAIN, "livedns"),
    DESTRUCTIVE,
    description=messages.ENABLE_LIVEDNS,
)
DNSSEC_ENABLE = DomainEndpoint(
    "domain_dnssec_enable", "POST", (*DOMAIN, "livedns", "dnssec"), WRITE
)
DNSSEC_DISABLE = DomainEndpoint(
    "domain_dnssec_disable",
    "DELETE",
    (*DOMAIN, "livedns", "dnssec"),
    DESTRUCTIVE,
    description=messages.DISABLE_DNSSEC,
)
DNSSEC_KEY_ADD = DomainEndpoint("domain_dnssec_key_add", "POST", (*DOMAIN, "dnskeys"), WRITE)
DNSSEC_KEYS_REPLACE = DomainEndpoint(
    "domain_dnssec_keys_replace",
    "PUT",
    (*DOMAIN, "dnskeys"),
    DESTRUCTIVE,
    description=messages.REPLACE_DNSSEC_KEYS,
)
DNSSEC_KEY_DELETE = DomainEndpoint(
    "domain_dnssec_key_delete",
    "DELETE",
    (*DOMAIN, "dnskeys", "{id}"),
    DESTRUCTIVE,
    description=messages.DELETE_DNSSEC_KEY,
)
GLUE_RECORD_CREATE = DomainEndpoint("domain_glue_record_create", "POST", (*DOMAIN, "hosts"), WRITE)
GLUE_RECORD_UPDATE = DomainEndpoint(
    "domain_glue_record_update", "PUT", (*DOMAIN, "hosts", "{host}"), WRITE
)
GLUE_RECORD_DELETE = DomainEndpoint(
    "domain_glue_record_delete",
    "DELETE",
    (*DOMAIN, "hosts", "{host}"),
    DESTRUCTIVE,
    description=messages.DELETE_GLUE_RECORD,
)
WEB_REDIRECTION_CREATE = DomainEndpoint(
    "domain_web_redirection_create", "POST", (*DOMAIN, "webredirs"), WRITE
)
WEB_REDIRECTION_UPDATE = DomainEndpoint(
    "domain_web_redirection_update", "PATCH", (*DOMAIN, "webredirs", "{host}"), WRITE
)
WEB_REDIRECTION_DELETE = DomainEndpoint(
    "domain_web_redirection_delete",
    "DELETE",
    (*DOMAIN, "webredirs", "{host}"),
    DESTRUCTIVE,
    description=messages.DELETE_WEB_REDIRECTION,
)
TAG_ADD = DomainEndpoint("domain_tag_add", "POST", (*DOMAIN, "tags"), WRITE)
TAGS_REPLACE = DomainEndpoint("domain_tags_replace", "PUT", (*DOMAIN, "tags"), WRITE)
TAGS_UPDATE = DomainEndpoint("domain_tags_update", "PATCH", (*DOMAIN, "tags"), WRITE)
TAGS_DELETE = DomainEndpoint(
    "domain_tags_delete", "DELETE", (*DOMAIN, "tags"), DESTRUCTIVE, description=messages.DELETE_TAGS
)
TRANSFER_OUT_ACCEPT = DomainEndpoint(
    "domain_transfer_out_accept",
    "POST",
    (*DOMAIN, "transferout"),
    DESTRUCTIVE,
    description=messages.ACCEPT_TRANSFER_OUT,
)
TRANSFER_OUT_DECLINE = DomainEndpoint(
    "domain_transfer_out_decline", "POST", (*DOMAIN, "transferout"), WRITE
)
TRANSFER_IN_RELAUNCH = DomainEndpoint(
    "domain_transfer_in_relaunch",
    "PUT",
    ("domain", "transferin", "{domain}"),
    WRITE,
    follow_up="domain_transfer_in_status",
)
TRANSFER_IN_CODE_UPDATE = DomainEndpoint(
    "domain_transfer_in_code_update",
    "PUT",
    ("domain", "transferin", "{domain}", "authinfo"),
    WRITE,
    description=messages.UPDATE_TRANSFER_CODE,
    secret_field="authinfo",  # noqa: S106 - name of the body field, not a secret
    secret_label=AUTHORIZATION_CODE,
)
TRANSFER_IN_RESEND = DomainEndpoint(
    "domain_transfer_in_resend", "POST", ("domain", "transferin", "{domain}", "foa"), WRITE
)

WRITE_ENDPOINTS: tuple[DomainEndpoint, ...] = (
    DELETE,
    AUTORENEW,
    TRANSFER_LOCK,
    AUTHORIZATION_CODE_RESET,
    REACHABILITY_RESEND,
    CLAIMS_ACCEPT,
    CONTACTS_UPDATE,
    OWNER_UPDATE,
    OWNER_CHANGE,
    OWNER_CHANGE_RESEND,
    NAMESERVERS_UPDATE,
    LIVEDNS_ENABLE,
    DNSSEC_ENABLE,
    DNSSEC_DISABLE,
    DNSSEC_KEY_ADD,
    DNSSEC_KEYS_REPLACE,
    DNSSEC_KEY_DELETE,
    GLUE_RECORD_CREATE,
    GLUE_RECORD_UPDATE,
    GLUE_RECORD_DELETE,
    WEB_REDIRECTION_CREATE,
    WEB_REDIRECTION_UPDATE,
    WEB_REDIRECTION_DELETE,
    TAG_ADD,
    TAGS_REPLACE,
    TAGS_UPDATE,
    TAGS_DELETE,
    TRANSFER_OUT_ACCEPT,
    TRANSFER_OUT_DECLINE,
    TRANSFER_IN_RELAUNCH,
    TRANSFER_IN_CODE_UPDATE,
    TRANSFER_IN_RESEND,
)
