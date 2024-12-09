"""Context processors for the Import_video module."""

from django.conf import settings as django_settings

USE_IMPORT_VIDEO = getattr(django_settings, "USE_IMPORT_VIDEO", False)

RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    django_settings, "RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY", True
)


def context_settings(request):
    """Return all context settings."""
    new_settings = {}
    new_settings["USE_IMPORT_VIDEO"] = USE_IMPORT_VIDEO
    new_settings["RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY"] = (
        RESTRICT_EDIT_IMPORT_VIDEO_ACCESS_TO_STAFF_ONLY
    )
    return new_settings
