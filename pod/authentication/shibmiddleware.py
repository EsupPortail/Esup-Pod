"""Esup-Pod Shibboleth middleware authentication."""

from shibboleth.middleware import ShibbolethRemoteUserMiddleware
from django.conf import settings
from pod.authentication.models import AFFILIATION_STAFF

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

AFFILIATION = getattr(
    settings,
    "AFFILIATION",
    (
        ("student", ""),
        ("faculty", ""),
        ("staff", ""),
        ("employee", ""),
        ("member", ""),
        ("affiliate", ""),
        ("alum", ""),
        ("library-walk-in", ""),
        ("researcher", ""),
        ("retired", ""),
        ("emeritus", ""),
        ("teacher", ""),
        ("registered-reader", ""),
    ),
)


class ShibbMiddleware(ShibbolethRemoteUserMiddleware):
    header = REMOTE_USER_HEADER

    def check_user_meta(self, user, shib_meta):
        """Check Shibboleth access rights with user's meta.

        Args:
            user: User,
            shib_meta dict
        Returns:
            bool
        """
        return (
            user
            and user.owner
            and shib_meta["affiliation"] in [A[0] for A in AFFILIATION]
            and user.owner.affiliation != shib_meta["affiliation"]
        )

    def is_staffable(self, user) -> bool:
        """Check that given user, his domain is in authorized domains of shibboleth staff.

        Args:
            user: User
        Returns:
            bool
        """
        if (
            SHIBBOLETH_STAFF_ALLOWED_DOMAINS is None
            or len(SHIBBOLETH_STAFF_ALLOWED_DOMAINS) == 0
        ):
            return True
        for d in SHIBBOLETH_STAFF_ALLOWED_DOMAINS:
            if user.username.endswith("@" + d):
                return True
        return False

    def make_profile(self, user, shib_meta) -> None:
        if ("affiliation" in shib_meta) and self.check_user_meta(user, shib_meta):
            user.owner.affiliation = shib_meta["affiliation"]
            user.owner.save()
        if self.is_staffable(user) and "affiliations" in shib_meta:
            for affiliation in shib_meta["affiliations"].split(";"):
                if affiliation in AFFILIATION_STAFF:
                    user.is_staff = True
                    user.save()
                    break
        return
