from django.conf import settings as django_settings

USE_RECORD_PREVIEW = getattr(django_settings, "USE_RECORD_PREVIEW", False)

ALLOW_MANUAL_RECORDING_CLAIMING = getattr(
    django_settings, "ALLOW_MANUAL_RECORDING_CLAIMING", False
)


def context_recorder_settings(request):
    """Return all context settings."""
    new_settings = {}
    new_settings["USE_RECORD_PREVIEW"] = USE_RECORD_PREVIEW
    new_settings["ALLOW_MANUAL_RECORDING_CLAIMING"] = ALLOW_MANUAL_RECORDING_CLAIMING
    return new_settings
