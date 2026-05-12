"""
Esup-Pod - Authentication constants.

Static data (choices tuples, default mappings) that are NOT configurable
via environment variables. These are domain constants, not deployment settings.
"""

from django.utils.translation import gettext_lazy as _

# --- Auth Type Choices ---
AUTH_TYPE = (
    ("local", _("local")),
    ("CAS", "CAS"),
    ("OIDC", "OIDC"),
    ("Shibboleth", "Shibboleth"),
)

# --- Affiliation Choices ---
AFFILIATION = (
    ("student", _("student")),
    ("faculty", _("faculty")),
    ("staff", _("staff")),
    ("employee", _("employee")),
    ("member", _("member")),
    ("affiliate", _("affiliate")),
    ("alum", _("alum")),
    ("library-walk-in", _("library-walk-in")),
    ("researcher", _("researcher")),
    ("retired", _("retired")),
    ("emeritus", _("emeritus")),
    ("teacher", _("teacher")),
    ("registered-reader", _("registered-reader")),
)
DEFAULT_AFFILIATION = AFFILIATION[0][0]

# --- Establishment Choices ---
ESTABLISHMENTS = (
    ("Etab_1", "Etab_1"),
    ("Etab_2", "Etab_2"),
)

# --- Default Attribute Mappings ---
DEFAULT_SHIBBOLETH_ATTRIBUTE_MAP = {
    "REMOTE_USER": (True, "username"),
    "Shibboleth-givenName": (True, "first_name"),
    "Shibboleth-sn": (False, "last_name"),
    "Shibboleth-mail": (False, "email"),
    "Shibboleth-primary-affiliation": (False, "affiliation"),
    "Shibboleth-unscoped-affiliation": (False, "affiliations"),
}

DEFAULT_LDAP_MAPPING_ATTRIBUTES = {
    "uid": "uid",
    "mail": "mail",
    "last_name": "sn",
    "first_name": "givenname",
    "primaryAffiliation": "eduPersonPrimaryAffiliation",
    "affiliations": "eduPersonAffiliation",
    "groups": "memberOf",
    "establishment": "establishment",
}

DEFAULT_LDAP_USER_SEARCH = ("ou=people,dc=example,dc=com", "(uid=%(uid)s)")
