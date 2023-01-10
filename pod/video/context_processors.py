from django.conf import settings as django_settings

CHUNK_SIZE = getattr(django_settings, "CHUNK_SIZE", 100000)
HIDE_USER_FILTER = getattr(django_settings, "HIDE_USER_FILTER", False)
OEMBED = getattr(django_settings, "OEMBED", False)
USE_STATS_VIEW = getattr(django_settings, "USE_STATS_VIEW", False)


def context_video_settings(request):
    new_settings = {}
    new_settings["CHUNK_SIZE"] = CHUNK_SIZE
    new_settings["HIDE_USER_FILTER"] = HIDE_USER_FILTER
    new_settings["OEMBED"] = OEMBED
    new_settings["USE_STATS_VIEW"] = USE_STATS_VIEW
    return new_settings
