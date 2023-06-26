from django.conf import settings as django_settings

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.models import Video

from django.db.models import Count, Sum
from django.db.models import Prefetch
from django.db.models import Q
from django.db.models import Exists
from django.db.models import OuterRef

from datetime import timedelta
from django.contrib.sites.shortcuts import get_current_site
from pod.main.models import AdditionalChannelTab
from pod.video_encode_transcript.models import EncodingVideo
from pod.video_encode_transcript.models import PlaylistVideo
from pod.video_encode_transcript.models import EncodingAudio

CHUNK_SIZE = getattr(django_settings, "CHUNK_SIZE", 100000)
HIDE_USER_FILTER = getattr(django_settings, "HIDE_USER_FILTER", False)
OEMBED = getattr(django_settings, "OEMBED", False)
USE_STATS_VIEW = getattr(django_settings, "USE_STATS_VIEW", False)

AVAILABLE_VIDEO_FILTER = {
    'encoding_in_progress': False,
    'is_draft': False,
    'sites': get_current_site(None),
}


def get_available_videos(request=None):
    """Get all videos available."""
    if request is not None:
        AVAILABLE_VIDEO_FILTER["site"] = get_current_site(request)
    vids = Video.objects.filter(**AVAILABLE_VIDEO_FILTER).defer(
        "video", "slug", "owner", "additional_owners", "description"
    ).filter(
        Q(Exists(
            EncodingVideo.objects.filter(
                video=OuterRef('pk'),
                encoding_format="video/mp4"
            )
        ))
        | Q(Exists(
            PlaylistVideo.objects.filter(
                video=OuterRef('pk'),
                name="playlist",
                encoding_format="application/x-mpegURL"
            )
        ))
        | Q(Exists(
            EncodingAudio.objects.filter(
                video=OuterRef('pk'),
                name="audio",
                encoding_format="video/mp4"
            )
        ))
    )
    return vids


def context_video_settings(request):
    new_settings = {}
    new_settings["CHUNK_SIZE"] = CHUNK_SIZE
    new_settings["HIDE_USER_FILTER"] = HIDE_USER_FILTER
    new_settings["OEMBED"] = OEMBED
    new_settings["USE_STATS_VIEW"] = USE_STATS_VIEW
    return new_settings


def context_navbar(request):
    channels = (
        Channel.objects.filter(
            visible=True,
            video__is_draft=False,
            add_channels_tab=None,
            site=get_current_site(request),
        )
        .distinct()
        .annotate(video_count=Count("video", distinct=True))
        .prefetch_related(
            Prefetch(
                "themes",
                queryset=Theme.objects.filter(
                    parentId=None, channel__site=get_current_site(request)
                )
                .distinct()
                .annotate(video_count=Count("video", distinct=True)),
            )
        )
    )

    add_channels_tab = AdditionalChannelTab.objects.all().prefetch_related(
        Prefetch(
            "channel_set",
            queryset=Channel.objects.filter(site=get_current_site(request))
            .distinct()
            .annotate(video_count=Count("video", distinct=True)),
        )
    )

    all_channels = (
        Channel.objects.all()
        .filter(site=get_current_site(request))
        .distinct()
        .annotate(video_count=Count("video", distinct=True))
        .prefetch_related(
            Prefetch(
                "themes",
                queryset=Theme.objects.filter(
                    channel__site=get_current_site(request)
                )
                .distinct()
                .annotate(video_count=Count("video", distinct=True)),
            )
        )
    )

    types = (
        Type.objects.filter(
            sites=get_current_site(request),
            video__is_draft=False,
            video__sites=get_current_site(request),
        )
        .distinct()
        .annotate(video_count=Count("video", distinct=True))
    )

    disciplines = (
        Discipline.objects.filter(
            site=get_current_site(request),
            video__is_draft=False,
            video__sites=get_current_site(request),
        )
        .distinct()
        .annotate(video_count=Count("video", distinct=True))
    )

    list_videos = get_available_videos()
    VIDEOS_COUNT = list_videos.count()
    VIDEOS_DURATION = (
        str(timedelta(seconds=list_videos.aggregate(
            Sum("duration")
        )["duration__sum"]))
        if list_videos.aggregate(Sum("duration"))["duration__sum"]
        else 0
    )

    return {
        "ALL_CHANNELS": all_channels,
        "ADD_CHANNELS_TAB": add_channels_tab,
        "CHANNELS": channels,
        "TYPES": types,
        "DISCIPLINES": disciplines,
        "VIDEOS_COUNT": VIDEOS_COUNT,
        "VIDEOS_DURATION": VIDEOS_DURATION,
    }
