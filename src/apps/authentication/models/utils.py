"""
Esup-Pod - Authentication model utilities.

User display logic and model choices. Constants are imported from constants.py,
configuration from conf.py.
"""

from django.contrib.auth.models import User

from ..conf import auth_settings
from ..constants import AFFILIATION, AUTH_TYPE, DEFAULT_AFFILIATION, ESTABLISHMENTS

# Re-export for backward compatibility with existing imports
__all__ = [
    "AUTH_TYPE",
    "AFFILIATION",
    "DEFAULT_AFFILIATION",
    "AFFILIATION_STAFF",
    "ESTABLISHMENTS",
    "HIDE_USERNAME",
    "get_name",
]

HIDE_USERNAME = auth_settings.hide_username
AFFILIATION_STAFF = auth_settings.affiliation_staff
SECRET_KEY = ""  # Kept for backward compat, should not be used from here


def get_name(self: User) -> str:
    """
    Return the user's full name, including the username if not hidden.

    Returns:
        str: The user's full name and username if not hidden.
    """
    if HIDE_USERNAME or not self.is_authenticated:
        return self.get_full_name().strip()
    return f"{self.get_full_name()} ({self.get_username()})".strip()


User.add_to_class("__str__", get_name)
