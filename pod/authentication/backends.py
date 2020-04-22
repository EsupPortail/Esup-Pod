from shibboleth.backends import ShibbolethRemoteUserBackend
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
