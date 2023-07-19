from pod.playlist.apps import FAVORITE_PLAYLIST_NAME
from pod.playlist.models import Playlist, PlaylistContent
from django.db.models import Sum
from pod.video.models import Video, ViewCount
from datetime import date
from django.core.cache import cache
from django.conf import settings
from json import dumps

CACHE_EXPIRATION = 2  # Cache expiration time in seconds


def get_videos_stats(videos, date_filter, mode=None):
    if not mode:
        video_stats = get_days_videos_stats(videos, date_filter)
    elif mode == "year":
        video_stats = get_years_videos_stats(videos, date_filter)
    return video_stats


def get_views_count(
    video_ids, date_filter=date.today(), years_only=False, day_only=False
):
    cache_key = f"views_count_{date_filter}_{years_only}_{day_only}"
    all_views = cache.get(cache_key)

    if all_views is None:
        all_views = {}
        if day_only:
            all_views["views_day"] = (
                ViewCount.objects.filter(
                    video_id__in=video_ids, date=date_filter
                ).aggregate(Sum("count"))["count__sum"]
                or 0
            )
        elif years_only:
            all_views["views_year"] = (
                ViewCount.objects.filter(
                    date__year=date_filter.year, video_id__in=video_ids
                ).aggregate(Sum("count"))["count__sum"]
                or 0
            )
        else:
            # view count since video was created
            all_views["views_since_created"] = (
                ViewCount.objects.filter(video_id__in=video_ids).aggregate(Sum("count"))[
                    "count__sum"
                ]
                or 0
            )

        cache.set(cache_key, all_views, CACHE_EXPIRATION)

    return all_views


def get_playlists_count(
    video_ids, date_filter=date.today(), years_only=False, day_only=False
):
    cache_key = f"playlists_count_{date_filter}_{years_only}_{day_only}"
    all_playlists = cache.get(cache_key)

    if all_playlists is None:
        all_playlists = {}
        if day_only:
            all_playlists["playlist_addition_day"] = PlaylistContent.objects.filter(
                video_id__in=video_ids, date_added__date=date_filter
            ).count()
        elif years_only:
            all_playlists["playlist_addition_year"] = PlaylistContent.objects.filter(
                video_id__in=video_ids, date_added__year=date_filter.year
            ).count()
        else:
            # playlist addition since video was created
            all_playlists[
                "playlist_addition_since_created"
            ] = PlaylistContent.objects.filter(video_id__in=video_ids).count()

        cache.set(cache_key, all_playlists, CACHE_EXPIRATION)

    return all_playlists


def get_favorites_count(
    video_ids, date_filter=date.today(), years_only=False, day_only=False
):
    cache_key = f"favorites_count_{date_filter}_{years_only}_{day_only}"
    all_favorites = cache.get(cache_key)

    if all_favorites is None:
        all_favorites = {}
        favorites_playlists = Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME)
        if day_only:
            all_favorites["favorites_day"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists,
                video_id__in=video_ids,
                date_added__date=date_filter,
            ).count()
        elif years_only:
            all_favorites["favorites_year"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists,
                video_id__in=video_ids,
                date_added__year=date_filter.year,
            ).count()
        else:
            all_favorites["favorites_since_created"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists, video_id__in=video_ids
            ).count()

        cache.set(cache_key, all_favorites, CACHE_EXPIRATION)

    return all_favorites


def get_days_videos_stats(video_list, date_filter=date.today()):
    all_video_stats = {"date": str(date_filter), "datas": {}}

    all_video_stats["datas"].update(
        get_views_count(video_list, date_filter, day_only=True)
    )
    if getattr(settings, "USE_PLAYLIST", True):
        all_video_stats["datas"].update(
            get_playlists_count(video_list, date_filter, day_only=True)
        )
    if getattr(settings, "USE_PLAYLIST", True) and getattr(
        settings, "USE_FAVORITES", True
    ):
        all_video_stats["datas"].update(
            get_favorites_count(video_list, date_filter, day_only=True)
        )

    return dumps(all_video_stats)


def get_years_videos_stats(video_list, date_filter=date.today()):
    all_years_videos_stats = {"year": date_filter.year, "datas": {}}

    all_years_videos_stats["datas"].update(
        get_views_count(video_list, date_filter, years_only=True)
    )
    if getattr(settings, "USE_PLAYLIST", True):
        all_years_videos_stats["datas"].update(
            get_playlists_count(video_list, date_filter, years_only=True)
        )
    if getattr(settings, "USE_PLAYLIST", True) and getattr(
        settings, "USE_FAVORITES", True
    ):
        all_years_videos_stats["datas"].update(
            get_favorites_count(video_list, date_filter, years_only=True)
        )

    return dumps(all_years_videos_stats)


def get_videos_status_stats(video_list) -> dict:
    stats = {}
    number_videos = len(video_list)
    draft_number = Video.objects.filter(id__in=video_list, is_draft=True).count()
    restricted_number = Video.objects.filter(
        id__in=video_list, is_restricted=True
    ).count()
    password_number = Video.objects.filter(
        id__in=video_list, password__isnull=False
    ).count()
    public_number = number_videos - draft_number - restricted_number - password_number

    stats["public"] = public_number
    stats["draft"] = draft_number
    stats["restricted"] = restricted_number
    stats["password"] = password_number
    return dumps(stats)
