from shibboleth.backends import ShibbolethRemoteUserBackend


class PodShibbolethRemoteUserBackend(ShibbolethRemoteUserBackend):
    @staticmethod
    def update_user_params(user, params):
        super(PodShibbolethRemoteUserBackend,
              PodShibbolethRemoteUserBackend).update_user_params(user, params)
        user.owner.auth_type = "Shibboleth"
        user.owner.save()
