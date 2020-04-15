from shibboleth.backends import ShibbolethRemoteUserBackend
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site


class ShibbBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super(ShibbBackend,
              ShibbBackend).update_user_params(user, params)
        user.owner.auth_type = "Shibboleth"
        user.owner.save()

    def setup_user(self, request, username, defaults):
        if self.create_unknown_user:
            user, created = User.objects.get_or_create(
                username=username,
                defaults=defaults,
                owner__sites=get_current_site(request))
            if created:
                user = self.handle_created_user(
                    request, user, owner__sites=get_current_site(request))
        else:
            try:
                user = User.objects.get(
                    username=username, owner__sites=get_current_site(request))
            except User.DoesNotExist:
                return
        return user
