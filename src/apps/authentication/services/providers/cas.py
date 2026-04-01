"""
Esup-Pod - CAS authentication provider service.
"""

import logging
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django_cas_ng.utils import get_cas_client

from ...conf import auth_settings
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

    if auth_settings.cas_force_change_username_case == "lower":
        username = username.lower()

    user, created = UserModel.objects.get_or_create(username=username)

    if created:
        user.set_unusable_password()
        user.save()

    populate_strategy = auth_settings.populate_user

    populator = UserPopulator(user)

    if populate_strategy == "CAS":
        populator.run("CAS", attributes)
    elif populate_strategy == "LDAP":
        populator.run("LDAP")
    else:
        pass

    return user
