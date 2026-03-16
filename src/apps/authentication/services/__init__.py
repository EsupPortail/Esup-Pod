from .core import (
    GROUP_STAFF,
    REMOTE_USER_HEADER,
    SHIBBOLETH_ATTRIBUTE_MAP,
    is_staff_affiliation,
)
from .providers import OIDCService, ShibbolethService, verify_cas_ticket
from .tokens import get_tokens_for_user
from .users import AccessGroupService, UserPopulator

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
