from ..django import settings_local
from ..env import env
from ..django.base import SECRET_KEY
from datetime import timedelta

USE_CAS = getattr(settings_local, "USE_CAS", False)
USE_LDAP = getattr(settings_local, "USE_LDAP", False)
USE_LOCAL_AUTH = getattr(settings_local, "USE_LOCAL_AUTH", True)

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
else:
    # Valeurs par défaut pour éviter les erreurs d'import si désactivé
    CAS_SERVER_URL = ""
    CAS_VERSION = '3'

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
else:

    LDAP_SERVER = {"url": "", "port": 389, "use_ssl": False}
    AUTH_LDAP_BIND_DN = ""
    AUTH_LDAP_BIND_PASSWORD = ""
    AUTH_LDAP_USER_SEARCH = ("", "")
    USER_LDAP_MAPPING_ATTRIBUTES = {}


ALLOWED_SUPERUSER_IPS = ["127.0.0.1", "10.0.0.0/8"]

AFFILIATION_STAFF = ("faculty", "employee", "staff")
CREATE_GROUP_FROM_AFFILIATION = True
CREATE_GROUP_FROM_GROUPS = True