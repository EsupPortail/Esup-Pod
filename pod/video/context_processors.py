from django.conf import settings as django_settings

from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.models import Video

from django.db.models import Count, Sum
from django.db.models import Q
from django.db.models import Exists
from django.db.models import OuterRef

from datetime import timedelta
from django.core.cache import cache
from django.contrib.sites.shortcuts import get_current_site
from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript.models import EncodingAudio

CHUNK_SIZE = getattr(django_settings, "CHUNK_SIZE", 100000)
HIDE_USER_FILTER = getattr(django_settings, "HIDE_USER_FILTER", False)
OEMBED = getattr(django_settings, "OEMBED", False)
USE_STATS_VIEW = getattr(django_settings, "USE_STATS_VIEW", False)
CACHE_VIDEO_DEFAULT_TIMEOUT = getattr(django_settings, "CACHE_VIDEO_DEFAULT_TIMEOUT", 600)
__AVAILABLE_VIDEO_FILTER__ = {
    "encoding_in_progress": False,
    "is_draft": False,
    "sites": 1,
}

CHANNELS_PER_BATCH = getattr(django_settings, "CHANNELS_PER_BATCH", 10)


def get_available_videos_filter(request=None):
    """Return the base filter to get the available videos of the site."""
    __AVAILABLE_VIDEO_FILTER__["sites"] = get_current_site(request)

    return (
        Video.objects.filter(**__AVAILABLE_VIDEO_FILTER__)
        .defer("video", "slug", "owner", "additional_owners", "description")
        .filter(
            Q(
                Exists(
                    EncodingVideo.objects.filter(
                        video=OuterRef("pk"), encoding_format="video/mp4"
                    )
                )
            )
            | Q(
                Exists(
                    PlaylistVideo.objects.filter(
                        video=OuterRef("pk"),
                        name="playlist",
                        encoding_format="application/x-mpegURL",
                    )
                )
            )
            | Q(
                Exists(
                    EncodingAudio.objects.filter(
                        video=OuterRef("pk"), name="audio", encoding_format="video/mp4"
                    )
                )
            )
        )
    )


def get_available_videos(request=None):
    """Get all videos available."""
    return get_available_videos_filter(request).distinct()


def context_video_settings(request):
    new_settings = {}
    new_settings["CHUNK_SIZE"] = CHUNK_SIZE
    new_settings["HIDE_USER_FILTER"] = HIDE_USER_FILTER
    new_settings["OEMBED"] = OEMBED
    new_settings["USE_STATS_VIEW"] = USE_STATS_VIEW
    return new_settings


def context_video_data(request):
    """Get video data in cache, if not, create and add it in cache."""
    types = cache.get("TYPES")
    if types is None:
        types = (
            Type.objects.filter(
                sites=get_current_site(request),
                video__is_draft=False,
                video__sites=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
        )
        cache.set("TYPES", types, timeout=CACHE_VIDEO_DEFAULT_TIMEOUT)

    disciplines = cache.get("DISCIPLINES")
    if disciplines is None:
        disciplines = (
            Discipline.objects.filter(
                site=get_current_site(request),
                video__is_draft=False,
                video__sites=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
        )
        cache.set("DISCIPLINES", disciplines, timeout=CACHE_VIDEO_DEFAULT_TIMEOUT)

    VIDEOS_COUNT = cache.get("VIDEOS_COUNT")
    VIDEOS_DURATION = cache.get("VIDEOS_DURATION")
    if VIDEOS_COUNT is None:
        v_filter = get_available_videos_filter(request)
        aggregate_videos = v_filter.aggregate(
            duration=Sum("duration"), number=Count("id")
        )
        VIDEOS_COUNT = aggregate_videos["number"]
        cache.set("VIDEOS_COUNT", VIDEOS_COUNT, timeout=CACHE_VIDEO_DEFAULT_TIMEOUT)
        VIDEOS_DURATION = (
            str(timedelta(seconds=aggregate_videos["duration"]))
            if aggregate_videos["duration"]
            else 0
        )
        cache.set("VIDEOS_DURATION", VIDEOS_DURATION, timeout=CACHE_VIDEO_DEFAULT_TIMEOUT)

    return {
        "TYPES": types,
        "DISCIPLINES": disciplines,
        "VIDEOS_COUNT": VIDEOS_COUNT,
        "VIDEOS_DURATION": VIDEOS_DURATION,
        "CHANNELS_PER_BATCH": CHANNELS_PER_BATCH,
    }
