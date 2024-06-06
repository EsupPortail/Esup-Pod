"""Esup-pod custom filters"""

from django import template

register = template.Library()


@register.filter(name="isinstance")
def isinstance(value, expected_instance):
    return value.__class__.__name__ in expected_instance


@register.filter(name="isempty")
def isempty(value):
    if isinstance(value, "str"):
        return value.strip() == ""
    return value is None


@register.filter(name="dict_get")
def dict_get(value: dict, key):
    """Get a dict value thanks to a key."""
    return value.get(key)
