from shibboleth.middleware import ShibbolethRemoteUserMiddleware


class PodShibbolethRemoteUserMiddleware(ShibbolethRemoteUserMiddleware):
    header = "HTTP_REMOTE_USER"
