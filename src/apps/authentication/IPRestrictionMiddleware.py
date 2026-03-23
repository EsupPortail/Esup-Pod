"""
Esup-Pod IP Restriction middleware.

Ensure that only allowed IPs can access superuser privileges.
"""

import ipaddress

from django.utils.translation import gettext_lazy as _

from django.conf import settings


def ip_in_allowed_range(ip) -> bool:
    """
    Check if the provided IP address is within the allowed ranges for superusers.

    This function reads the `ALLOWED_SUPERUSER_IPS` setting from the Django 
    configuration. If the list is empty, it allows all IP addresses. Otherwise, 
    it checks if the given IP matches any of the specified addresses or networks.

    Args:
        ip (str): The IP address to check.

    Returns:
        bool: True if the IP is allowed or if no restrictions are defined, 
              False otherwise.
    """

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
            if is_allowed(ip_obj, allowed):
                return True
        except ValueError:
            continue
    return False


def is_allowed(ip_obj, allowed):
    """
    Determine if an IP object matches a specific allowed entry.

    The entry can be a single IP address or a network in CIDR notation.

    Args:
        ip_obj (ipaddress.IPv4Address or ipaddress.IPv6Address): The IP object 
            to validate.
        allowed (str): The allowed IP entry (e.g., '192.168.1.1' or '192.168.1.0/24').

    Returns:
        bool: True if the IP matches the entry, False otherwise.
    """
    if "/" in allowed:
        net = ipaddress.ip_network(allowed, strict=False)
        if ip_obj in net:
            return True
    else:
        if ip_obj == ipaddress.ip_address(allowed):
            return True
    return False


class IPRestrictionMiddleware:
    """
    Middleware to enforce IP-based restrictions for Django superusers in Esup-Pod.

    If a superuser logs in from an unauthorized IP address, their superuser 
    privileges are temporarily revoked for the duration of the request, 
    and their display name is updated to indicate the restriction.
    """

    def __init__(self, get_response) -> None:
        """
        Initialize the middleware with the standard Django get_response callable.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Process each request to check superuser IP restrictions.

        If the user is an authenticated superuser, validates their IP address. 
        If unauthorized, it strips their superuser status and modifies their 
        last name for visual feedback.
        """
        ip = request.META.get("REMOTE_ADDR")
        user = request.user

        if user.is_authenticated and user.is_superuser:
            if not ip_in_allowed_range(ip):
                user.is_superuser = False
                user.last_name = _(
                    "%(last_name)s (Restricted - IP %(ip)s not allowed)"
                ) % {"last_name": user.last_name, "ip": ip}

        return self.get_response(request)
