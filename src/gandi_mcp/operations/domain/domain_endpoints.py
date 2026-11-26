# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Catalogue of the Gandi Domain API endpoints (https://api.gandi.net/docs/domains/)."""

from gandi_mcp.operations.domain.domain_endpoint import DomainEndpoint
from gandi_mcp.operations.operation_category import OperationCategory

READ = OperationCategory.READ
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
