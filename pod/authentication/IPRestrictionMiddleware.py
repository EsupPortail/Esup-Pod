"""
Esup-Pod IP Restriction middleware.

Ensure that only allowed IPs can access superuser privileges.
"""

import ipaddress
from django.utils.translation import gettext_lazy as _


def ip_in_allowed_range(ip) -> bool:
    """Make sure the IP is one of the authorized ones."""
    from django.conf import settings
    ALLOWED_SUPERUSER_IPS = getattr(settings, "ALLOWED_SUPERUSER_IPS", [])

    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False

    if not ALLOWED_SUPERUSER_IPS:
        # Allow every clients
        return True

    for allowed in ALLOWED_SUPERUSER_IPS:
        try:
            if '/' in allowed:
                net = ipaddress.ip_network(allowed, strict=False)
                if ip_obj in net:
                    return True
            else:
                if ip_obj == ipaddress.ip_address(allowed):
                    return True
        except ValueError:
            continue
    return False


class IPRestrictionMiddleware:
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR')
        user = request.user

        if user.is_authenticated and user.is_superuser:
            if not ip_in_allowed_range(ip):
                user.is_superuser = False
                user.last_name = _(
                    "%(last_name)s (Restricted - IP %(ip)s not allowed)"
                ) % {"last_name": user.last_name, "ip": ip}

        return self.get_response(request)
