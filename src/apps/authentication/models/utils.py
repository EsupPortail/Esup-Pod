from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

if getattr(settings, "USE_PODFILE", False):
    from src.apps.utils.models.CustomImageModel import CustomImageModel # TODO : change import path when files will be implamented
else:
    from src.apps.utils.models.CustomImageModel import CustomImageModel

HIDE_USERNAME = getattr(settings, "HIDE_USERNAME", False)

AUTH_TYPE = getattr(
    settings,
    "AUTH_TYPE",
    (
        ("local", _("local")),
        ("CAS", "CAS"),
        ("OIDC", "OIDC"),
        ("Shibboleth", "Shibboleth"),
    ),
)
AFFILIATION = getattr(
    settings,
    "AFFILIATION",
    (
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
    ),
)
DEFAULT_AFFILIATION = AFFILIATION[0][0]
AFFILIATION_STAFF = getattr(
    settings, "AFFILIATION_STAFF", ("faculty", "employee", "staff")
)
ESTABLISHMENTS = getattr(
    settings,
    "ESTABLISHMENTS",
    (
        ("Etab_1", "Etab_1"),
        ("Etab_2", "Etab_2"),
    ),
)
SECRET_KEY = getattr(settings, "SECRET_KEY", "")

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
