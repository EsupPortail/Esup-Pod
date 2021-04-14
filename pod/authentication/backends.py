from shibboleth.backends import ShibbolethRemoteUserBackend
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings


class ShibbBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super(ShibbBackend,
              ShibbBackend).update_user_params(user, params)
        user.owner.auth_type = "Shibboleth"
        if get_current_site(None) not in user.owner.sites.all():
            user.owner.sites.add(get_current_site(None))
        user.owner.save()


# Fetch profile claims to fill User model
# ref: https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html\
# #changing-how-django-users-are-created
OIDC_CLAIM_GIVEN_NAME = getattr(
    settings, 'OIDC_CLAIM_GIVEN_NAME', "given_name")
OIDC_CLAIM_FAMILY_NAME = getattr(
    settings, 'OIDC_CLAIM_FAMILY_NAME', "family_name")


class OIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCBackend, self).create_user(claims)

        user.first_name = claims.get(OIDC_CLAIM_GIVEN_NAME, '')
        user.last_name = claims.get(OIDC_CLAIM_FAMILY_NAME, '')
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get(OIDC_CLAIM_GIVEN_NAME, '')
        user.last_name = claims.get(OIDC_CLAIM_FAMILY_NAME, '')
        user.save()

        user.owner.auth_type = "OIDC"
        user.owner.save()

        return user
