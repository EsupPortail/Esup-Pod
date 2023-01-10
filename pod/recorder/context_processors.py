from django.conf import settings as django_settings

USE_RECORD_PREVIEW = getattr(django_settings, "USE_RECORD_PREVIEW", False)


def context_recorder_settings(request):
    """Return all context settings."""
    new_settings = {}
    new_settings["USE_RECORD_PREVIEW"] = USE_RECORD_PREVIEW
    return new_settings
