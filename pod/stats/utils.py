from pod.playlist.apps import FAVORITE_PLAYLIST_NAME
from pod.playlist.models import Playlist, PlaylistContent
from django.db.models import Sum
from pod.video.models import Video, ViewCount
from datetime import date
from django.core.cache import cache
from django.conf import settings

CACHE_EXPIRATION = 60  # Cache expiration time in seconds


def get_videos_stats(videos, date_filter):
    video_stats = []
    stats = get_all_videos_stats(videos, date_filter)
    video_stat = {
        **stats,
    }
    video_stats.append(video_stat)
    return video_stats


def get_views_count(video_ids, date_filter):
    cache_key = f"views_count_{date_filter}"
    all_views = cache.get(cache_key)

    if all_views is None:
        all_views = {}

        # view count in day
        all_views["day"] = ViewCount.objects.filter(
            video_id__in=video_ids, date=date_filter
        ).aggregate(Sum("count"))["count__sum"] or 0

        # view count of all videos for the year
        all_views["all_view_year"] = ViewCount.objects.filter(
            video_id__in=video_ids, date__year=date_filter.year
        ).aggregate(Sum("count"))["count__sum"] or 0

        # view count in month
        all_views["month"] = ViewCount.objects.filter(
            video_id__in=video_ids,
            date__year=date_filter.year,
            date__month=date_filter.month,
        ).aggregate(Sum("count"))["count__sum"] or 0

        # view count in year
        all_views["year"] = ViewCount.objects.filter(
            date__year=date_filter.year, video_id__in=video_ids
        ).aggregate(Sum("count"))["count__sum"] or 0

        # view count since video was created
        all_views["since_created"] = ViewCount.objects.filter(
            video_id__in=video_ids
        ).aggregate(Sum("count"))["count__sum"] or 0

        cache.set(cache_key, all_views, CACHE_EXPIRATION)

    return all_views


def get_playlists_count(video_ids, date_filter):
    cache_key = f"playlists_count_{date_filter}"
    all_playlists = cache.get(cache_key)

    if all_playlists is None:
        all_playlists = {}

        # favorite count of all videos for the year
        all_playlists["all_playlists_year"] = PlaylistContent.objects.filter(
            date_added__year=date_filter.year, video_id__in=video_ids
        ).count()

        # playlist addition in day
        all_playlists["playlist_day"] = PlaylistContent.objects.filter(
            video_id__in=video_ids, date_added__date=date_filter
        ).count()

        # playlist addition in month
        all_playlists["playlist_month"] = PlaylistContent.objects.filter(
            video_id__in=video_ids,
            date_added__year=date_filter.year,
            date_added__month=date_filter.month,
        ).count()

        # playlist addition in year
        all_playlists["playlist_year"] = PlaylistContent.objects.filter(
            video_id__in=video_ids, date_added__year=date_filter.year
        ).count()

        # playlist addition since video was created
        all_playlists["playlist_since_created"] = PlaylistContent.objects.filter(
            video_id__in=video_ids
        ).count()

        cache.set(cache_key, all_playlists, CACHE_EXPIRATION)

    return all_playlists


def get_favorites_count(video_ids, date_filter):
    cache_key = f"favorites_count_{date_filter}"
    all_favorites = cache.get(cache_key)

    if all_favorites is None:
        all_favorites = {}

        favorites_playlists = Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME)

        # favorite addition in day
        all_favorites["fav_day"] = PlaylistContent.objects.filter(
            playlist__in=favorites_playlists,
            video_id__in=video_ids,
            date_added__date=date_filter,
        ).count()

        # favorite count of all videos for the year
        all_favorites["all_fav_year"] = PlaylistContent.objects.filter(
            playlist__in=favorites_playlists,
            date_added__year=date_filter.year,
            video_id__in=video_ids,
        ).count()

        # favorite addition in month
        all_favorites["fav_month"] = PlaylistContent.objects.filter(
            playlist__in=favorites_playlists,
            video_id__in=video_ids,
            date_added__year=date_filter.year,
            date_added__month=date_filter.month,
        ).count()

        # favorite addition in year
        all_favorites["fav_year"] = PlaylistContent.objects.filter(
            playlist__in=favorites_playlists,
            video_id__in=video_ids,
            date_added__year=date_filter.year,
        ).count()

        # favorite addition since video was created
        all_favorites["fav_since_created"] = PlaylistContent.objects.filter(
            playlist__in=favorites_playlists, video_id__in=video_ids
        ).count()

        cache.set(cache_key, all_favorites, CACHE_EXPIRATION)

    return all_favorites


def get_all_videos_stats(video_ids, date_filter=date.today()):
    cache_key = f"all_videos_stats_{video_ids}_{date_filter}"
    all_video_stats = cache.get(cache_key)

    if all_video_stats is None:
        all_video_stats = {}
        all_video_stats["date"] = str(date_filter)
        all_video_stats["all_year"] = str(date_filter.year)

        all_video_stats.update(get_views_count(video_ids, date_filter))
        if getattr(settings, "USE_PLAYLIST", True):
            all_video_stats.update(get_playlists_count(video_ids, date_filter))
        if getattr(settings, "USE_PLAYLIST", True) and getattr(settings, "USE_FAVORITES", True):
            all_video_stats.update(get_favorites_count(video_ids, date_filter))

        cache.set(cache_key, all_video_stats, CACHE_EXPIRATION)

    return all_video_stats


def get_videos_status_stats(video_list) -> dict:
    stats = {}
    number_videos = len(video_list)
    draft_number = Video.objects.filter(id__in=video_list, is_draft=True).count()
    restricted_number = Video.objects.filter(
        id__in=video_list, is_restricted=True).count()
    password_number = Video.objects.filter(
        id__in=video_list, password__isnull=False).count()
    public_number = number_videos - draft_number - restricted_number - password_number

    stats['public'] = public_number
    stats['draft'] = draft_number
    stats['restricted'] = restricted_number
    stats['password'] = password_number
    return stats
