# SPDX-FileCopyrightText: 2026 bobyone
# SPDX-License-Identifier: GPL-2.0-or-later
"""Descriptions of the confirmed domain operations, shown in their confirmation."""

from gandi_mcp.i18n.message import N_

DELETE_DOMAIN = N_("delete the domain {domain}: it will be lost for good")
UPDATE_OWNER = N_("change the owner details of {domain}")
UPDATE_OWNER_EMAIL = N_(
    "change the owner details of {domain}, including its email address: you authorize "
    "Gandi to act as your Designated Agent under the ICANN rules for this change"
)
UNLOCK_TRANSFER = N_("unlock {domain}: it can then be transferred to another registrar")
RESET_AUTHORIZATION_CODE = N_(
    "reset the authorization code of {domain}: the current code stops working"
)
REPLACE_TAGS = N_("replace all the tags of {domain}")
DECLINE_TRANSFER_OUT = N_("decline the transfer of {domain} to another registrar")
DOMAIN_AUTHORIZATION_CODE = N_(
    "Authorization code of the domain (shown in the Gandi administration)"
)
CHANGE_OWNER = N_(
    "give the domain {domain} to a new owner; Gandi may charge for it depending on the "
    "extension, and the amount is not known in advance"
)
UPDATE_NAMESERVERS = N_(
    "replace the nameservers of {domain}; a wrong list makes the domain unreachable"
)
ENABLE_LIVEDNS = N_("switch {domain} to the Gandi LiveDNS nameservers, replacing its current ones")
DISABLE_DNSSEC = N_("disable DNSSEC for {domain}")
REPLACE_DNSSEC_KEYS = N_("replace all the DNSSEC keys of {domain}")
DELETE_DNSSEC_KEY = N_("delete the DNSSEC key {id} of {domain}")
DELETE_GLUE_RECORD = N_("delete the glue record {host} of {domain}")
DELETE_WEB_REDIRECTION = N_("delete the web redirection of {host}")
REPLACE_WITH_WEB_REDIRECTION = N_("redirect {host} to {url}, replacing its current DNS record")
DELETE_TAGS = N_("remove all the tags of {domain}")
ACCEPT_TRANSFER_OUT = N_(
    "accept the transfer of {domain} to another registrar: it will leave Gandi"
)
UPDATE_TRANSFER_CODE = N_("update the authorization code of the pending transfer of {domain}")
