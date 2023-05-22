from django.conf import settings as django_settings

USE_FAVORITES = getattr(django_settings, "USE_FAVORITES", True)


def context_settings(request):
    """Return all context settings for favorite app"""
    new_settings = {}
    new_settings["USE_FAVORITES"] = USE_FAVORITES
    return new_settings
