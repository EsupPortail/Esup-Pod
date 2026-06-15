"""
Esup-Pod - Core authentication services and shared constants.

This module contains configuration settings and utility functions used by
the different authentication providers.
"""

from ..conf import auth_settings

GROUP_STAFF = auth_settings.affiliation_staff

CREATE_GROUP_FROM_AFFILIATION = auth_settings.create_group_from_affiliation

REMOTE_USER_HEADER = auth_settings.remote_user_header
SHIBBOLETH_ATTRIBUTE_MAP = auth_settings.shibboleth_attribute_map
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = auth_settings.shibboleth_staff_allowed_domains

OIDC_CLAIM_GIVEN_NAME = auth_settings.oidc_claim_given_name
OIDC_CLAIM_FAMILY_NAME = auth_settings.oidc_claim_family_name
OIDC_CLAIM_PREFERRED_USERNAME = auth_settings.oidc_claim_preferred_username
OIDC_DEFAULT_AFFILIATION = auth_settings.oidc_default_affiliation
OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = auth_settings.oidc_default_access_group_code_names

USER_LDAP_MAPPING_ATTRIBUTES = auth_settings.ldap_mapping_attributes

AUTH_LDAP_USER_SEARCH = (
    auth_settings.ldap_user_search_base,
    auth_settings.ldap_user_search_filter,
)


def is_staff_affiliation(affiliation) -> bool:
    """Check if user affiliation correspond to AFFILIATION_STAFF."""
    return affiliation in auth_settings.affiliation_staff
