"""Esup-Pod custom tags for templates."""
from django import template
from django.conf import settings
from pod.main.models import Configuration
import json

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
