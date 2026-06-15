from .providers import OIDCService, ShibbolethService, verify_cas_ticket
from .tokens import get_tokens_for_user
from .users import AccessGroupService, UserPopulator
from ..conf import auth_settings

GROUP_STAFF = auth_settings.affiliation_staff

REMOTE_USER_HEADER = auth_settings.remote_user_header
SHIBBOLETH_ATTRIBUTE_MAP = auth_settings.shibboleth_attribute_map


def is_staff_affiliation(affiliation: str) -> bool:
    """Check if user affiliation corresponds to staff affiliations."""
    return affiliation in auth_settings.affiliation_staff


__all__ = [
    "is_staff_affiliation",
    "GROUP_STAFF",
    "REMOTE_USER_HEADER",
    "SHIBBOLETH_ATTRIBUTE_MAP",
    "get_tokens_for_user",
    "AccessGroupService",
    "UserPopulator",
    "verify_cas_ticket",
    "ShibbolethService",
    "OIDCService",
]
