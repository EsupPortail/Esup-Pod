from django.conf import settings
from ..models.utils import AFFILIATION_STAFF, DEFAULT_AFFILIATION

GROUP_STAFF = AFFILIATION_STAFF

CREATE_GROUP_FROM_AFFILIATION = getattr(
    settings, "CREATE_GROUP_FROM_AFFILIATION", False
)

REMOTE_USER_HEADER = getattr(settings, "REMOTE_USER_HEADER", "REMOTE_USER")
SHIBBOLETH_ATTRIBUTE_MAP = getattr(
    settings,
    "SHIBBOLETH_ATTRIBUTE_MAP",
    {
        "REMOTE_USER": (True, "username"),
        "Shibboleth-givenName": (True, "first_name"),
        "Shibboleth-sn": (False, "last_name"),
        "Shibboleth-mail": (False, "email"),
        "Shibboleth-primary-affiliation": (False, "affiliation"),
        "Shibboleth-unscoped-affiliation": (False, "affiliations"),
    },
)
SHIBBOLETH_STAFF_ALLOWED_DOMAINS = getattr(
    settings, "SHIBBOLETH_STAFF_ALLOWED_DOMAINS", None
)

OIDC_CLAIM_GIVEN_NAME = getattr(settings, "OIDC_CLAIM_GIVEN_NAME", "given_name")
OIDC_CLAIM_FAMILY_NAME = getattr(settings, "OIDC_CLAIM_FAMILY_NAME", "family_name")
OIDC_CLAIM_PREFERRED_USERNAME = getattr(
    settings, "OIDC_CLAIM_PREFERRED_USERNAME", "preferred_username"
)
OIDC_DEFAULT_AFFILIATION = getattr(
    settings, "OIDC_DEFAULT_AFFILIATION", DEFAULT_AFFILIATION
)
OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES = getattr(
    settings, "OIDC_DEFAULT_ACCESS_GROUP_CODE_NAMES", []
)

USER_LDAP_MAPPING_ATTRIBUTES = getattr(
    settings,
    "USER_LDAP_MAPPING_ATTRIBUTES",
    {
        "uid": "uid",
        "mail": "mail",
        "last_name": "sn",
        "first_name": "givenname",
        "primaryAffiliation": "eduPersonPrimaryAffiliation",
        "affiliations": "eduPersonAffiliation",
        "groups": "memberOf",
        "establishment": "establishment",
    },
)

AUTH_LDAP_USER_SEARCH = getattr(
    settings,
    "AUTH_LDAP_USER_SEARCH",
    ("ou=people,dc=univ,dc=fr", "(uid=%(uid)s)"),
)

def is_staff_affiliation(affiliation) -> bool:
    """Check if user affiliation correspond to AFFILIATION_STAFF."""
    return affiliation in AFFILIATION_STAFF
