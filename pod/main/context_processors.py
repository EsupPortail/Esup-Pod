from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured


def context_settings(request):
    new_settings = {}
    for attr in getattr(django_settings, 'TEMPLATE_VISIBLE_SETTINGS', []):
        try:
            new_settings[attr] = getattr(django_settings, attr)
        except:
            m = "TEMPLATE_VISIBLE_SETTINGS: '{0}' does not exist".format(attr)
            raise ImproperlyConfigured

    return new_settings
