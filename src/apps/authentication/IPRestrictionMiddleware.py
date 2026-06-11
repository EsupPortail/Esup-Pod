"""
Esup-Pod IP Restriction middleware.

Ensure that only allowed IPs can access superuser privileges.
"""

import ipaddress

from ipware import get_client_ip
from django.utils.translation import gettext_lazy as _
from .conf import auth_settings


def ip_in_allowed_range(ip) -> bool:
    """Check if the provided IP is within the allowed ranges for superusers."""

    # Filter out empty or whitespace-only entries
    ALLOWED_SUPERUSER_IPS = [
        ip_range.strip()
        for ip_range in auth_settings.allowed_superuser_ips
        if ip_range and ip_range.strip()
    ]

    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError:
        return False

    if not ALLOWED_SUPERUSER_IPS:
        # Allow every clients
        return True

    for allowed in ALLOWED_SUPERUSER_IPS:
        try:
            if is_allowed(ip_obj, allowed):
                return True
        except ValueError:
            continue
    return False


def is_allowed(ip_obj, allowed):
    """Determine if an IP object matches a specific allowed entry (IP or CIDR)."""
    if "/" in allowed:
        net = ipaddress.ip_network(allowed, strict=False)
        if ip_obj in net:
            return True
    else:
        if ip_obj == ipaddress.ip_address(allowed):
            return True
    return False


class IPRestrictionMiddleware:
    """Middleware to enforce IP-based restrictions for Django superusers."""

    def __init__(self, get_response) -> None:
        """Initialize the middleware."""
        self.get_response = get_response

    def __call__(self, request):
        """Process the request and enforce IP restrictions for superusers."""
        ip, is_routable = get_client_ip(request)
        user = request.user

        if user.is_authenticated and user.is_superuser:
            if not ip or not ip_in_allowed_range(ip):
                user.is_superuser = False
                user.last_name = _(
                    "%(last_name)s (Restricted - IP %(ip)s not allowed)"
                ) % {"last_name": user.last_name, "ip": ip or "unknown"}

        return self.get_response(request)
