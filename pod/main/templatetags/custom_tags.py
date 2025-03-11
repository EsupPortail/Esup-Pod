"""Esup-Pod custom tags for templates."""

from django import template
from django.conf import settings
from pod.main.models import Configuration
import json

from urllib.parse import urlparse, urlunparse, parse_qs

register = template.Library()


@register.simple_tag
def get_setting(name, default=""):
    """Get a setting value."""
    return getattr(settings, name, default)


@register.simple_tag
def get_maintenance_welcome():
    """Return Welcome text for maintenance."""
    return Configuration.objects.get(key="maintenance_text_welcome").value


@register.simple_tag
def str_to_dict(value):
    """Convert Json string to python dict."""
    return json.loads(value)


@register.filter
def get_type(value):
    return type(value)


@register.simple_tag
def get_url_referrer(request):
    """Return the authentication login url with cleaned referrer."""
    # Split url into uri components

    # Temp for fix
    if isinstance(request, str) or request is None:
        return "/"

    uri = urlparse(request.build_absolute_uri())
    # Parse the query string part of uri
    query = parse_qs(uri.query, keep_blank_values=True)

    # Recursively get only the last "next" or "referrer" param in query
    for param in ["next", "referrer"]:
        while param in query:
            uri = urlparse(query[param][0])
            query = parse_qs(uri.query, keep_blank_values=True)

    return "?referrer=%s" % urlunparse(uri)
