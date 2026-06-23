from django.contrib.auth.models import User

from .AccessGroup import AccessGroup
from .GroupSite import GroupSite
from .Owner import Owner
from .ServerRole import ServerRole
from .utils import (
    AFFILIATION,
    AUTH_TYPE,
    ESTABLISHMENTS,
    HIDE_USERNAME,
)


def get_name(self: User) -> str:
    """
    Returns the user's full name, including the username if it is not hidden.
    Overrides Django's default __str__ method.
    """
    if HIDE_USERNAME or not self.is_authenticated:
        name = self.get_full_name().strip()
        return name if name else self.get_username()

    full_name = self.get_full_name().strip()
    if full_name:
        return f"{full_name} ({self.get_username()})"
    return self.get_username()


User.add_to_class("__str__", get_name)

__all__ = [
    "AFFILIATION",
    "AUTH_TYPE",
    "ESTABLISHMENTS",
    "Owner",
    "AccessGroup",
    "GroupSite",
    "ServerRole",
]
