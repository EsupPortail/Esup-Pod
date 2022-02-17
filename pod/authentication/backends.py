from shibboleth.backends import ShibbolethRemoteUserBackend
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

CREATE_GROUP_FROM_AFFILIATION = getattr(settings, "CREATE_GROUP_FROM_AFFILIATION", False)

AFFILIATION_STAFF = getattr(
    settings, "AFFILIATION_STAFF", ("faculty", "employee", "staff")
)


class ShibbBackend(ShibbolethRemoteUserBackend):
    def authenticate(self, request, remote_user, shib_meta):
        """
        The username passed as ``remote_user`` is considered trusted.  Use the
        username to get or create the user.
        """
        if not remote_user:
            return
        username = self.clean_username(remote_user)
        field_names = [x.name for x in User._meta.get_fields()]
        shib_user_params = dict(
            [(k, shib_meta[k]) for k in field_names if k in shib_meta]
        )

        user = self.setup_user(
            request=request, username=username, defaults=shib_user_params
        )
        if user:
            super(ShibbBackend, ShibbBackend).update_user_params(
                user=user, params=shib_user_params
            )
            self.update_owner_params(user=user, params=shib_meta)
            return user if self.user_can_authenticate(user) else None

    @staticmethod
    def update_owner_params(user, params):
        user.owner.auth_type = "Shibboleth"
        if get_current_site(None) not in user.owner.sites.all():
            user.owner.sites.add(get_current_site(None))
        user.owner.save()
        # affiliation
        user.owner.affiliation = params["affiliation"]
        if params["affiliation"] in AFFILIATION_STAFF:
            user.is_staff = True
        if CREATE_GROUP_FROM_AFFILIATION:
            group, group_created = Group.objects.get_or_create(name=params["affiliation"])
            user.groups.add(group)
        user.save()
        user.owner.save()


# Fetch profile claims to fill User model
# ref: https://mozilla-django-oidc.readthedocs.io/en/stable/installation.html\
# #changing-how-django-users-are-created
OIDC_CLAIM_GIVEN_NAME = getattr(settings, "OIDC_CLAIM_GIVEN_NAME", "given_name")
OIDC_CLAIM_FAMILY_NAME = getattr(settings, "OIDC_CLAIM_FAMILY_NAME", "family_name")


class OIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        user = super(OIDCBackend, self).create_user(claims)

        user.first_name = claims.get(OIDC_CLAIM_GIVEN_NAME, "")
        user.last_name = claims.get(OIDC_CLAIM_FAMILY_NAME, "")
        user.save()

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get(OIDC_CLAIM_GIVEN_NAME, "")
        user.last_name = claims.get(OIDC_CLAIM_FAMILY_NAME, "")
        user.save()

        user.owner.auth_type = "OIDC"
        user.owner.save()

        return user
