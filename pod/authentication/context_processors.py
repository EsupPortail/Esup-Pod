from django.conf import settings as django_settings

SHIB_NAME = getattr(django_settings, "SHIB_NAME", "Identify Federation")


def context_authentication_settings(request):
    new_settings = {}
    new_settings["SHIB_NAME"] = SHIB_NAME
    return new_settings
