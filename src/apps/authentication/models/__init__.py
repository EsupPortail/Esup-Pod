from django.contrib.auth.models import User

from .AccessGroup import AccessGroup
from .GroupSite import GroupSite
from .Owner import Owner
from .utils import (
    AFFILIATION,
    AFFILIATION_STAFF,
    AUTH_TYPE,
    DEFAULT_AFFILIATION,
    ESTABLISHMENTS,
    HIDE_USERNAME,
)


def get_name(self: User) -> str:
    """
    Retourne le nom complet de l'utilisateur, incluant le username s'il n'est pas caché.
    Remplace la méthode __str__ par défaut de Django.
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
    "AFFILIATION_STAFF",
    "DEFAULT_AFFILIATION",
    "AUTH_TYPE",
    "ESTABLISHMENTS",
    "Owner",
    "AccessGroup",
    "GroupSite",
]
