from shibboleth.backends import ShibbolethRemoteUserBackend


class ShibbBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super(ShibbBackend,
              ShibbBackend).update_user_params(user, params)
        user.owner.auth_type = "Shibboleth"
        user.owner.save()
