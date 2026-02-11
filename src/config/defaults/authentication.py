"""
Authentication defaults.
Source of truth for default values for Authentication app.
"""

# Feature Flags
USE_LOCAL_AUTH = True
USE_CAS = False
USE_LDAP = False
USE_SHIB = False
USE_OIDC = False

# CAS Defaults
CAS_SERVER_URL = "https://cas.univ-lille.fr"
CAS_VERSION = "3"
CAS_FORCE_CHANGE_USERNAME_CASE = "lower"
CAS_APPLY_ATTRIBUTES_TO_USER = True
CAS_ADMIN_REDIRECT = False

# LDAP Defaults
LDAP_SERVER_URL = "ldap://ldap.univ.fr"
LDAP_SERVER_PORT = 389
LDAP_SERVER_USE_SSL = False
LDAP_BIND_DN = "cn=pod,ou=app,dc=univ,dc=fr"

# OIDC Defaults
OIDC_OP_TOKEN_ENDPOINT = "https://auth.example.com/oidc/token"
OIDC_OP_USER_ENDPOINT = "https://auth.example.com/oidc/userinfo"
OIDC_RP_CLIENT_ID = "mon-client-id"

# UI
HIDE_USERNAME = False

# Security
ALLOWED_SUPERUSER_IPS = ["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]
AFFILIATION_STAFF = ("faculty", "employee", "staff")
CREATE_GROUP_FROM_AFFILIATION = True
CREATE_GROUP_FROM_GROUPS = True
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = []

LDAP_BIND_PASSWORD = ""
LDAP_USER_SEARCH_BASE = "ou=people,dc=univ,dc=fr"
LDAP_USER_SEARCH_FILTER = "(uid=%(uid)s)"
LDAP_MAPPING_ATTRIBUTES = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "primaryAffiliation": "eduPersonPrimaryAffiliation",
    "affiliations": "eduPersonAffiliation",
    "groups": "memberOf",
    "establishment": "establishment",
}

OIDC_RP_CLIENT_SECRET = "mon-secret"
OIDC_CLAIM_GIVEN_NAME = "given_name"
OIDC_CLAIM_FAMILY_NAME = "family_name"
OIDC_CLAIM_PREFERRED_USERNAME = "preferred_username"
OIDC_DEFAULT_AFFILIATION = "member"
OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = []

SHIB_SECURE_HEADER = None
SHIB_SECURE_VALUE = "secure"
SHIBBOLETH_ATTRIBUTE_MAP = {
    "REMOTE_USER": (True, "username"),
    "Shibboleth-givenName": (True, "first_name"),
    "Shibboleth-sn": (False, "last_name"),
    "Shibboleth-mail": (False, "email"),
    "Shibboleth-primary-affiliation": (False, "affiliation"),
    "Shibboleth-unscoped-affiliation": (False, "affiliations"),
}

USE_ESTABLISHMENT_FIELD = False
REMOTE_USER_HEADER = "REMOTE_USER"
