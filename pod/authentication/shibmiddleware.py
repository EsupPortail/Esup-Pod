from shibboleth.middleware import ShibbolethRemoteUserMiddleware
from django.conf import settings

REMOTE_USER_HEADER = getattr(
    settings, 'REMOTE_USER_HEADER', "REMOTE_USER")


class ShibbMiddleware(ShibbolethRemoteUserMiddleware):
    header = REMOTE_USER_HEADER
