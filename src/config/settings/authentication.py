import os
from datetime import timedelta
from ..env import env
from ..django.base import SECRET_KEY
try:
    from ..django.settings_local import USE_LOCAL_AUTH, USE_CAS, USE_LDAP, USE_SHIB, USE_OIDC
except ImportError:
    USE_LOCAL_AUTH = True
    USE_CAS = False
    USE_LDAP = False
    USE_SHIB = False
    USE_OIDC = False

# Derived configuration
POPULATE_USER = "CAS" if USE_CAS else "LDAP" if USE_LDAP else None

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

AUTHENTICATION_BACKENDS = []

if USE_LOCAL_AUTH:
    AUTHENTICATION_BACKENDS.append('django.contrib.auth.backends.ModelBackend')

if USE_CAS:
    AUTHENTICATION_BACKENDS.append('django_cas_ng.backends.CASBackend')

if USE_CAS:
    CAS_SERVER_URL = "https://cas.univ-lille.fr"
    CAS_VERSION = '3'
    CAS_FORCE_CHANGE_USERNAME_CASE = 'lower'
    CAS_APPLY_ATTRIBUTES_TO_USER = True

if USE_LDAP:
    LDAP_SERVER = {
        "url": "ldap://ldap.univ.fr",
        "port": 389,
        "use_ssl": False
    }

    AUTH_LDAP_BIND_DN = "cn=pod,ou=app,dc=univ,dc=fr"
    AUTH_LDAP_BIND_PASSWORD = env("AUTH_LDAP_BIND_PASSWORD", default="")

    AUTH_LDAP_USER_SEARCH = ("ou=people,dc=univ,dc=fr", "(uid=%(uid)s)")

    USER_LDAP_MAPPING_ATTRIBUTES = {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliations": "eduPersonAffiliation",
        "groups": "memberOf",
        "establishment": "establishment",
    }

ALLOWED_SUPERUSER_IPS = ["127.0.0.1", "10.0.0.0/8"]
AFFILIATION_STAFF = ("faculty", "employee", "staff")
CREATE_GROUP_FROM_AFFILIATION = True
CREATE_GROUP_FROM_GROUPS = True

# TODO: Verifiy implementation
if USE_CAS and USE_SHIB:
    SHIBBOLETH_ATTRIBUTE_MAP = {
    "REMOTE_USER": (True, "username"),
    "Shibboleth-givenName": (True, "first_name"),
    "Shibboleth-sn": (False, "last_name"),
    "Shibboleth-mail": (False, "email"),
    "Shibboleth-primary-affiliation": (False, "affiliation"),
    "Shibboleth-unscoped-affiliation": (False, "affiliations"),
    }

    SHIBBOLETH_STAFF_ALLOWED_DOMAINS = []

if USE_CAS and USE_OIDC:
    OIDC_CLAIM_GIVEN_NAME = "given_name"
    OIDC_CLAIM_FAMILY_NAME = "family_name"
    OIDC_CLAIM_PREFERRED_USERNAME = "preferred_username"

    OIDC_DEFAULT_AFFILIATION = "member"
    OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = []
    OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", "mon-client-id")
    OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", "mon-secret")

    OIDC_OP_TOKEN_ENDPOINT = os.environ.get(
        "OIDC_OP_TOKEN_ENDPOINT", 
        "https://auth.example.com/oidc/token"
    )

    OIDC_OP_USER_ENDPOINT = os.environ.get(
        "OIDC_OP_USER_ENDPOINT", 
        "https://auth.example.com/oidc/userinfo"
    )