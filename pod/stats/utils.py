from collections import Counter
from django.shortcuts import get_object_or_404
from pod.meeting.models import Meeting
from pod.playlist.apps import FAVORITE_PLAYLIST_NAME
from pod.playlist.models import Playlist, PlaylistContent
from django.db.models import Sum
from pod.playlist.utils import (
    get_favorite_playlist_for_user,
    get_number_video_in_playlist,
    get_playlist_list_for_user,
)
from pod.podfile.models import UserFolder
from pod.video.context_processors import get_available_videos
from pod.video.models import Video, ViewCount
from datetime import date
from django.core.cache import cache
from django.conf import settings
from json import dumps
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site

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


def total_time_videos(request, video_list: None) -> str:
    if video_list:
        total_duration = video_list.aggregate(Sum("duration"))["duration__sum"]
    else:
        total_duration = get_available_videos(request).aggregate(Sum("duration"))[
            "duration__sum"
        ]
    return str(timedelta(seconds=total_duration)) if total_duration else "0"


def number_videos(request, video_list: None) -> int:
    if video_list:
        number_videos = video_list.count()
    else:
        number_videos = get_available_videos(request).count()
    return number_videos


def number_playlist(user: User) -> int:
    """
    Get the number of playlists for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of playlist.
    """
    return get_playlist_list_for_user(user).count()


def number_files(user: User) -> int:
    user_home_folder = get_object_or_404(UserFolder, name="home", owner=user)
    return len(user_home_folder.get_all_files())


def number_favorites(user: User) -> int:
    favorites = get_favorite_playlist_for_user(user)
    return get_number_video_in_playlist(favorites)


def number_meetings(user: User) -> int:
    return Meeting.objects.filter(owner=user).count()


def number_channels(request) -> int:
    site = get_current_site(request)
    channels = request.user.owners_channels.all().filter(site=site)
    return channels.count()


def get_most_common_type_discipline(video_list):
    if len(video_list) > 0:
        type_counter = Counter()
        discipline_counter = Counter()

        for video in video_list:
            if video.type and video.type.slug != "other":
                type_counter[video.type] += 1
            if video.discipline.exists():
                for discipline in video.discipline.all():
                    discipline_counter[discipline] += 1

        most_common_type = type_counter.most_common(1)[0][0] if type_counter else None
        most_common_discipline = (
            discipline_counter.most_common(1)[0][0] if discipline_counter else None
        )
    else:
        most_common_type = None
        most_common_discipline = None
    return most_common_type, most_common_discipline
