"""
Esup-Pod - Authentication defaults.
Source of truth for default values for Authentication app.
"""

from datetime import timedelta
from config.env import env

# Feature Flags
USE_LOCAL_AUTH = True
USE_CAS = False
USE_LDAP = False
USE_SHIB = False
USE_OIDC = False

# ggignore-start
# gitguardian:ignore
SECRET_KEY = env("SECRET_KEY", default="ta-cle-secrete-par-defaut")  # nosec
# ggignore-end

# JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# Authentication Backends
AUTHENTICATION_BACKENDS = []

if USE_LOCAL_AUTH:
    AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.ModelBackend")

if USE_CAS:
    AUTHENTICATION_BACKENDS.append("django_cas_ng.backends.CASBackend")

if USE_LDAP:
    AUTHENTICATION_BACKENDS.append("django_auth_ldap.backend.LDAPBackend")

if USE_OIDC:
    AUTHENTICATION_BACKENDS.append("mozilla_django_oidc.auth.OIDCAuthenticationBackend")

if USE_SHIB:
    AUTHENTICATION_BACKENDS.append("django.contrib.auth.backends.RemoteUserBackend")

# CAS Defaults
CAS_SERVER_URL = env("CAS_SERVER_URL", default="https://cas.univ-lille.fr")
CAS_VERSION = env("CAS_VERSION", default="3")
CAS_FORCE_CHANGE_USERNAME_CASE = env("CAS_FORCE_CHANGE_USERNAME_CASE", default="lower")
CAS_APPLY_ATTRIBUTES_TO_USER = env.bool("CAS_APPLY_ATTRIBUTES_TO_USER", default=True)
CAS_ADMIN_REDIRECT = env.bool("CAS_ADMIN_REDIRECT", default=False)

# LDAP Defaults
LDAP_SERVER_URL = env("LDAP_SERVER_URL", default="ldap://ldap.univ.fr")
LDAP_SERVER_PORT = env.int("LDAP_SERVER_PORT", default=389)
LDAP_SERVER_USE_SSL = env.bool("LDAP_SERVER_USE_SSL", default=False)
LDAP_BIND_DN = env("LDAP_BIND_DN", default="cn=pod,ou=app,dc=univ,dc=fr")
LDAP_BIND_PASSWORD = env("LDAP_BIND_PASSWORD", default="")

# OIDC Defaults
OIDC_OP_TOKEN_ENDPOINT = env(
    "OIDC_OP_TOKEN_ENDPOINT", default="https://auth.example.com/oidc/token"
)
OIDC_OP_USER_ENDPOINT = env(
    "OIDC_OP_USER_ENDPOINT", default="https://auth.example.com/oidc/userinfo"
)
OIDC_RP_CLIENT_ID = env("OIDC_RP_CLIENT_ID", default="mon-client-id")
OIDC_RP_CLIENT_SECRET = env("OIDC_RP_CLIENT_SECRET", default="mon-secret")
OIDC_NAME = env("OIDC_NAME", default="OpenID Connect")

# UI
HIDE_USERNAME = env.bool("HIDE_USERNAME", default=False)

# Security
ALLOWED_SUPERUSER_IPS = env.list(
    "ALLOWED_SUPERUSER_IPS",
    default=["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
)
AFFILIATION_STAFF = ("faculty", "employee", "staff")
CREATE_GROUP_FROM_AFFILIATION = True
CREATE_GROUP_FROM_GROUPS = True
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = []

LDAP_USER_SEARCH_BASE = env("LDAP_USER_SEARCH_BASE", default="ou=people,dc=univ,dc=fr")
LDAP_USER_SEARCH_FILTER = env("LDAP_USER_SEARCH_FILTER", default="(uid=%(uid)s)")
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
SHIB_NAME = env("SHIB_NAME", default="Identify Federation")

USE_ESTABLISHMENT_FIELD = False
REMOTE_USER_HEADER = "REMOTE_USER"
