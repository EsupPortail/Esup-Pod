"""Esup-Pod Authentication signals."""

from django.conf import settings
from django.dispatch import receiver
from django_cas_ng.signals import cas_user_authenticated, cas_user_logout

from pod.authentication.populatedCASbackend import populateUser


@receiver(cas_user_authenticated)
def cas_user_authenticated_callback(sender, **kwargs) -> None:
    """Callback for CAS user authenticated signal."""
    args = {}
    args.update(kwargs)
    user = args.get("user")
    attributes = args.get("attributes", [])
    DEBUG = getattr(settings, "DEBUG", True)
    if DEBUG:
        print(
            """cas_user_authenticated_callback:
        user: %s
        created: %s
        attributes: %s
        """
            % (
                user,
                args.get("created"),
                attributes,
            )
        )
    if user:
        populateUser(user, attributes)


@receiver(cas_user_logout)
def cas_user_logout_callback(sender, **kwargs) -> None:
    """Callback for CAS user logout signal."""
    args = {}
    args.update(kwargs)
    print(
        """cas_user_logout_callback:
    user: %s
    session: %s
    ticket: %s
    """
        % (args.get("user"), args.get("session"), args.get("ticket"))
    )
