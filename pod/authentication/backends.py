from shibboleth.backends import ShibbolethRemoteUserBackend


class PodShibbolethRemoteUserBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super().update_user_params(user, params)
        user.owner.auth_type = "shibboleth"
