# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Catalogue of the Gandi Domain API endpoints (https://api.gandi.net/docs/domains/)."""

from gandi_mcp.operations.domain import domain_messages as messages
from gandi_mcp.operations.domain.billable.messages import AUTHORIZATION_CODE
from gandi_mcp.operations.endpoint.endpoint import Endpoint
from gandi_mcp.operations.operation_category import OperationCategory

READ = OperationCategory.READ
WRITE = OperationCategory.WRITE
DESTRUCTIVE = OperationCategory.DESTRUCTIVE
DOMAIN = ("domain", "domains", "{domain}")
PAGE = frozenset({"page", "per_page"})

CHECK_AVAILABILITY = Endpoint(
    "domain_check_availability",
    "GET",
    ("domain", "check"),
    READ,
    frozenset({"name", "processes", "currency", "country", "lang", "sharing_id", "max_duration"}),
)
LIST_TLDS = Endpoint("domain_list_tlds", "GET", ("domain", "tlds"), READ, PAGE | {"category"})
TLD_DETAILS = Endpoint("domain_tld_details", "GET", ("domain", "tlds", "{tld}"), READ)
LIST_DOMAINS = Endpoint(
    "domain_list",
    "GET",
    ("domain", "domains"),
    READ,
    PAGE | {"fqdn", "tld", "nameserver", "sort_by", "sharing_id"},
)
DETAILS = Endpoint("domain_details", "GET", DOMAIN, READ)
CREATION_STATUS = Endpoint(
    "domain_creation_status",
    "GET",
    (*DOMAIN, "createstatus"),
    READ,
    completes_with_see_other=True,
)
CONTACTS = Endpoint("domain_contacts", "GET", (*DOMAIN, "contacts"), READ)
NAMESERVERS = Endpoint("domain_nameservers", "GET", (*DOMAIN, "nameservers"), READ)
LIVEDNS_STATUS = Endpoint("domain_livedns_status", "GET", (*DOMAIN, "livedns"), READ)
DNSSEC_STATUS = Endpoint("domain_dnssec_status", "GET", (*DOMAIN, "livedns", "dnssec"), READ)
DNSSEC_KEYS = Endpoint("domain_dnssec_keys", "GET", (*DOMAIN, "dnskeys"), READ, PAGE)
GLUE_RECORDS = Endpoint("domain_glue_records", "GET", (*DOMAIN, "hosts"), READ, PAGE)
GLUE_RECORD = Endpoint("domain_glue_record", "GET", (*DOMAIN, "hosts", "{host}"), READ)
WEB_REDIRECTIONS = Endpoint("domain_web_redirections", "GET", (*DOMAIN, "webredirs"), READ, PAGE)
WEB_REDIRECTION = Endpoint("domain_web_redirection", "GET", (*DOMAIN, "webredirs", "{host}"), READ)
TAGS = Endpoint("domain_tags", "GET", (*DOMAIN, "tags"), READ)
RENEWAL_INFO = Endpoint("domain_renewal_info", "GET", (*DOMAIN, "renew"), READ)
RESTORE_INFO = Endpoint("domain_restore_info", "GET", (*DOMAIN, "restore"), READ)
CLAIMS = Endpoint("domain_claims", "GET", (*DOMAIN, "claims"), READ)
OWNER_CHANGE_STATUS = Endpoint(
    "domain_owner_change_status",
    "GET",
    ("domain", "changeowner", "{domain}"),
    READ,
    frozenset({"sharing_id"}),
)
TRANSFER_IN_STATUS = Endpoint(
    "domain_transfer_in_status", "GET", ("domain", "transferin", "{domain}"), READ
)
# A POST that only checks whether a transfer is possible: it changes nothing.
TRANSFER_IN_CHECK = Endpoint(
    "domain_transfer_in_check",
    "POST",
    ("domain", "transferin", "{domain}", "available"),
    READ,
)

READ_ENDPOINTS: tuple[Endpoint, ...] = (
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
DELETE = Endpoint(
    "domain_delete", "DELETE", DOMAIN, DESTRUCTIVE, description=messages.DELETE_DOMAIN
)
AUTORENEW = Endpoint("domain_autorenew_update", "PATCH", (*DOMAIN, "autorenew"), WRITE)
TRANSFER_LOCK = Endpoint("domain_transfer_lock", "PATCH", (*DOMAIN, "status"), WRITE)
TRANSFER_UNLOCK = Endpoint(
    "domain_transfer_unlock",
    "PATCH",
    (*DOMAIN, "status"),
    DESTRUCTIVE,
    description=messages.UNLOCK_TRANSFER,
)
AUTHORIZATION_CODE_RESET = Endpoint(
    "domain_authorization_code_reset",
    "PUT",
    (*DOMAIN, "authinfo"),
    DESTRUCTIVE,
    description=messages.RESET_AUTHORIZATION_CODE,
)
REACHABILITY_RESEND = Endpoint(
    "domain_reachability_resend", "PATCH", (*DOMAIN, "reachability"), WRITE
)
CLAIMS_ACCEPT = Endpoint("domain_claims_accept", "POST", (*DOMAIN, "claims"), WRITE)
CONTACTS_UPDATE = Endpoint("domain_contacts_update", "PATCH", (*DOMAIN, "contacts"), WRITE)
OWNER_UPDATE = Endpoint(
    "domain_owner_update",
    "PUT",
    (*DOMAIN, "contacts", "owner"),
    DESTRUCTIVE,
    description=messages.UPDATE_OWNER,
    supports_dry_run=True,
)
# Same request, with the email unlocked: Gandi needs the ICANN designated-agent consent.
OWNER_EMAIL_UPDATE = Endpoint(
    "domain_owner_email_update",
    "PUT",
    (*DOMAIN, "contacts", "owner"),
    DESTRUCTIVE,
    description=messages.UPDATE_OWNER_EMAIL,
)
OWNER_CHANGE = Endpoint(
    "domain_owner_change",
    "POST",
    ("domain", "changeowner", "{domain}"),
    DESTRUCTIVE,
    description=messages.CHANGE_OWNER,
    supports_dry_run=True,
    follow_up="domain_owner_change_status",
)
OWNER_CHANGE_RESEND = Endpoint(
    "domain_owner_change_resend", "POST", ("domain", "changeowner", "{domain}", "foa"), WRITE
)
NAMESERVERS_UPDATE = Endpoint(
    "domain_nameservers_update",
    "PUT",
    (*DOMAIN, "nameservers"),
    DESTRUCTIVE,
    description=messages.UPDATE_NAMESERVERS,
)
LIVEDNS_ENABLE = Endpoint(
    "domain_livedns_enable",
    "POST",
    (*DOMAIN, "livedns"),
    DESTRUCTIVE,
    description=messages.ENABLE_LIVEDNS,
)
DNSSEC_ENABLE = Endpoint("domain_dnssec_enable", "POST", (*DOMAIN, "livedns", "dnssec"), WRITE)
DNSSEC_DISABLE = Endpoint(
    "domain_dnssec_disable",
    "DELETE",
    (*DOMAIN, "livedns", "dnssec"),
    DESTRUCTIVE,
    description=messages.DISABLE_DNSSEC,
)
DNSSEC_KEY_ADD = Endpoint("domain_dnssec_key_add", "POST", (*DOMAIN, "dnskeys"), WRITE)
DNSSEC_KEYS_REPLACE = Endpoint(
    "domain_dnssec_keys_replace",
    "PUT",
    (*DOMAIN, "dnskeys"),
    DESTRUCTIVE,
    description=messages.REPLACE_DNSSEC_KEYS,
)
DNSSEC_KEY_DELETE = Endpoint(
    "domain_dnssec_key_delete",
    "DELETE",
    (*DOMAIN, "dnskeys", "{id}"),
    DESTRUCTIVE,
    description=messages.DELETE_DNSSEC_KEY,
)
GLUE_RECORD_CREATE = Endpoint("domain_glue_record_create", "POST", (*DOMAIN, "hosts"), WRITE)
GLUE_RECORD_UPDATE = Endpoint(
    "domain_glue_record_update", "PUT", (*DOMAIN, "hosts", "{host}"), WRITE
)
GLUE_RECORD_DELETE = Endpoint(
    "domain_glue_record_delete",
    "DELETE",
    (*DOMAIN, "hosts", "{host}"),
    DESTRUCTIVE,
    description=messages.DELETE_GLUE_RECORD,
)
WEB_REDIRECTION_CREATE = Endpoint(
    "domain_web_redirection_create", "POST", (*DOMAIN, "webredirs"), WRITE
)
WEB_REDIRECTION_REPLACE = Endpoint(
    "domain_web_redirection_replace",
    "POST",
    (*DOMAIN, "webredirs"),
    DESTRUCTIVE,
    description=messages.REPLACE_WITH_WEB_REDIRECTION,
)
WEB_REDIRECTION_UPDATE = Endpoint(
    "domain_web_redirection_update", "PATCH", (*DOMAIN, "webredirs", "{host}"), WRITE
)
WEB_REDIRECTION_DELETE = Endpoint(
    "domain_web_redirection_delete",
    "DELETE",
    (*DOMAIN, "webredirs", "{host}"),
    DESTRUCTIVE,
    description=messages.DELETE_WEB_REDIRECTION,
)
TAG_ADD = Endpoint("domain_tag_add", "POST", (*DOMAIN, "tags"), WRITE)
TAGS_REPLACE = Endpoint(
    "domain_tags_replace",
    "PUT",
    (*DOMAIN, "tags"),
    DESTRUCTIVE,
    description=messages.REPLACE_TAGS,
)
TAGS_UPDATE = Endpoint("domain_tags_update", "PATCH", (*DOMAIN, "tags"), WRITE)
TAGS_DELETE = Endpoint(
    "domain_tags_delete", "DELETE", (*DOMAIN, "tags"), DESTRUCTIVE, description=messages.DELETE_TAGS
)
TRANSFER_OUT_ACCEPT = Endpoint(
    "domain_transfer_out_accept",
    "POST",
    (*DOMAIN, "transferout"),
    DESTRUCTIVE,
    description=messages.ACCEPT_TRANSFER_OUT,
    secret_field="authinfo",  # noqa: S106 - name of the body field, not a secret
    secret_label=messages.DOMAIN_AUTHORIZATION_CODE,
)
TRANSFER_OUT_DECLINE = Endpoint(
    "domain_transfer_out_decline",
    "POST",
    (*DOMAIN, "transferout"),
    WRITE,
    description=messages.DECLINE_TRANSFER_OUT,
    secret_field="authinfo",  # noqa: S106 - name of the body field, not a secret
    secret_label=messages.DOMAIN_AUTHORIZATION_CODE,
)
TRANSFER_IN_RELAUNCH = Endpoint(
    "domain_transfer_in_relaunch",
    "PUT",
    ("domain", "transferin", "{domain}"),
    WRITE,
    follow_up="domain_transfer_in_status",
)
TRANSFER_IN_CODE_UPDATE = Endpoint(
    "domain_transfer_in_code_update",
    "PUT",
    ("domain", "transferin", "{domain}", "authinfo"),
    WRITE,
    frozenset({"sharing_id"}),
    description=messages.UPDATE_TRANSFER_CODE,
    secret_field="authinfo",  # noqa: S106 - name of the body field, not a secret
    secret_label=AUTHORIZATION_CODE,
)
TRANSFER_IN_RESEND = Endpoint(
    "domain_transfer_in_resend", "POST", ("domain", "transferin", "{domain}", "foa"), WRITE
)

WRITE_ENDPOINTS: tuple[Endpoint, ...] = (
    DELETE,
    AUTORENEW,
    TRANSFER_LOCK,
    TRANSFER_UNLOCK,
    AUTHORIZATION_CODE_RESET,
    REACHABILITY_RESEND,
    CLAIMS_ACCEPT,
    CONTACTS_UPDATE,
    OWNER_UPDATE,
    OWNER_EMAIL_UPDATE,
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
    WEB_REDIRECTION_REPLACE,
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
