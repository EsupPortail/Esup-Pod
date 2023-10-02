from django.core.management.base import BaseCommand
from django.core.cache import cache
from datetime import timedelta
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import Count, Sum
from django.conf import settings as django_settings

from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.context_processors import get_available_videos_filter

CACHE_VIDEO_DEFAULT_TIMEOUT = getattr(django_settings, "CACHE_VIDEO_DEFAULT_TIMEOUT", 60)


class Command(BaseCommand):
    help = "Store video data in django cache : " \
        + "types, discipline, video count and videos duration"

    def handle(self, *args, **options):
        request = None
        types = (
            Type.objects.filter(
                sites=get_current_site(request),
                video__is_draft=False,
                video__sites=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
        )
        cache.delete('TYPES')
        cache.set("TYPES", types, timeout=None)

        disciplines = (
            Discipline.objects.filter(
                site=get_current_site(request),
                video__is_draft=False,
                video__sites=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
        )
        cache.delete('DISCIPLINES')
        cache.set("DISCIPLINES", disciplines, timeout=None)

        v_filter = get_available_videos_filter(request)

        aggregate_videos = v_filter.aggregate(duration=Sum("duration"), number=Count("id"))

        VIDEOS_COUNT = aggregate_videos["number"]
        cache.delete('VIDEOS_COUNT')
        cache.set("VIDEOS_COUNT", VIDEOS_COUNT, timeout=None)
        VIDEOS_DURATION = (
            str(timedelta(seconds=aggregate_videos["duration"]))
            if aggregate_videos["duration"]
            else 0
        )
        cache.delete('VIDEOS_DURATION')
        cache.set("VIDEOS_DURATION", VIDEOS_DURATION, timeout=None)

        self.stdout.write(
            self.style.SUCCESS('Successfully store video data in cache')
        )
