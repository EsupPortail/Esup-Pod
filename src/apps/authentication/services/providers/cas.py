import logging
from typing import Optional, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from django_cas_ng.utils import get_cas_client

from ..users import UserPopulator

UserModel = get_user_model()
logger = logging.getLogger(__name__)


def verify_cas_ticket(ticket: str, service_url: str) -> Optional[Any]:
    """
    Verifies the CAS service ticket using django-cas-ng utils.
    Then populates user using UserPopulator.
    """
    client = get_cas_client(service_url=service_url)
    username, attributes, _ = client.verify_ticket(ticket)

    if not username:
        logger.warning("CAS ticket validation failed")
        return None

    if getattr(settings, "CAS_FORCE_CHANGE_USERNAME_CASE", "lower") == "lower":
        username = username.lower()

    user, created = UserModel.objects.get_or_create(username=username)

    if created:
        user.set_unusable_password()
        user.save()

    # Determine usage strategy
    populate_strategy = getattr(settings, "POPULATE_USER", None)

    populator = UserPopulator(user)

    if populate_strategy == "CAS":
        populator.run("CAS", attributes)
    elif populate_strategy == "LDAP":
        populator.run("LDAP")
    else:
        # Minimal init if no external source strategy selected
        pass

    return user
