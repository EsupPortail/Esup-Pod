from django import template
from django.conf import settings
from pod.main.models import Configuration
import json

register = template.Library()


@register.simple_tag
def get_setting(name, default=""):
    return getattr(settings, name, default)


@register.simple_tag
def get_maintenance_welcome():
    return Configuration.objects.get(key="maintenance_text_welcome").value


@register.simple_tag
def str_to_dict(value):
    return json.loads(value)
