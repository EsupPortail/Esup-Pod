from shibboleth.backends import ShibbolethRemoteUserBackend
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.sites.shortcuts import get_current_site


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
# ref: https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html#changing-how-django-users-are-created
class OIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCBackend, self).create_user(claims)

        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.save()

        user.owner.auth_type = "OIDC"
        user.owner.save()

        return user
