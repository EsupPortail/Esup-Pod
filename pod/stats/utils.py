"""Esup-Pod stats utilities."""
from collections import Counter
from typing import List
from datetime import date, timedelta

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings

from pod.meeting.models import Meeting
from pod.playlist.models import Playlist, PlaylistContent
from pod.playlist.apps import FAVORITE_PLAYLIST_NAME
from pod.playlist.utils import (
    get_favorite_playlist_for_user,
    get_number_video_in_playlist,
)
from pod.podfile.models import UserFolder
from pod.video.context_processors import get_available_videos
from pod.video.models import Channel, Theme, Video, ViewCount

from json import dumps

CACHE_EXPIRATION = 300  # Cache expiration time in seconds


def get_videos_stats(
    video_list: List[Video], date_filter: date, mode: str = None
) -> dict:
    """
    Get aggregated statistics data for a list of videos based on the specified date filter and mode.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date): The date filter to apply.
        mode (str, optional): The mode for data aggregation. Defaults to None.

    Returns:
        dict: A dictionary containing the aggregated statistics data.
    """
    if not mode:
        video_stats = get_days_videos_stats(video_list, date_filter)
    elif mode == "year":
        video_stats = get_years_videos_stats(video_list, date_filter)
    return video_stats


def get_views_count(
    video_list: List[Video],
    date_filter: date = date.today(),
    years_only: bool = False,
    day_only: bool = False,
) -> dict:
    """
    Get the total views count for a list of videos based on the specified date filter and options.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date, optional): The date filter to apply. Defaults to today's date.
        years_only (bool, optional): If True, calculate views count for years only. Defaults to False.
        day_only (bool, optional): If True, calculate views count for a specific day only. Defaults to False.

    Returns:
        dict: A dictionary containing the aggregated views count data.
    """
    cache_key = f"views_count_{date_filter}_{years_only}_{day_only}"
    all_views = cache.get(cache_key)

    if all_views is None:
        all_views = {}
        if day_only:
            all_views["views_day"] = (
                ViewCount.objects.filter(
                    video_id__in=video_list, date=date_filter
                ).aggregate(Sum("count"))["count__sum"]
                or 0
            )
        elif years_only:
            all_views["views_year"] = (
                ViewCount.objects.filter(
                    date__year=date_filter.year, video_id__in=video_list
                ).aggregate(Sum("count"))["count__sum"]
                or 0
            )
        else:
            # view count since video was created
            all_views["views_since_created"] = (
                ViewCount.objects.filter(video_id__in=video_list).aggregate(Sum("count"))[
                    "count__sum"
                ]
                or 0
            )

        cache.set(cache_key, all_views, CACHE_EXPIRATION)

    return all_views


def get_playlists_count(
    video_list: List[Video],
    date_filter: date = date.today(),
    years_only: bool = False,
    day_only: bool = False,
) -> dict:
    """
    Get the total playlists count for a list of videos based on the specified date filter and options.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date, optional): The date filter to apply. Defaults to today's date.
        years_only (bool, optional): If True, calculate playlist addition for years only. Defaults to False.
        day_only (bool, optional): If True, calculate playlist addition for a specific day only. Defaults to False.

    Returns:
        dict: A dictionary containing the aggregated playlists count data.
    """
    cache_key = f"playlists_count_{date_filter}_{years_only}_{day_only}"
    all_playlists = cache.get(cache_key)

    if all_playlists is None:
        all_playlists = {}
        if day_only:
            all_playlists["playlist_addition_day"] = PlaylistContent.objects.filter(
                video_id__in=video_list, date_added__date=date_filter
            ).count()
        elif years_only:
            all_playlists["playlist_addition_year"] = PlaylistContent.objects.filter(
                video_id__in=video_list, date_added__year=date_filter.year
            ).count()
        else:
            # playlist addition since video was created
            all_playlists[
                "playlist_addition_since_created"
            ] = PlaylistContent.objects.filter(video_id__in=video_list).count()

        cache.set(cache_key, all_playlists, CACHE_EXPIRATION)

    return all_playlists


def get_favorites_count(
    video_list: List[Video],
    date_filter: date = date.today(),
    years_only: bool = False,
    day_only: bool = False,
) -> dict:
    """
    Get the total favorites count for a list of videos based on the specified date filter and options.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date, optional): The date filter to apply. Defaults to today's date.
        years_only (bool, optional): If True, calculate favorites count for years only. Defaults to False.
        day_only (bool, optional): If True, calculate favorites count for a specific day only. Defaults to False.

    Returns:
        dict: A dictionary containing the aggregated favorites count data.
    """
    cache_key = f"favorites_count_{date_filter}_{years_only}_{day_only}"
    all_favorites = cache.get(cache_key)

    if all_favorites is None:
        all_favorites = {}
        favorites_playlists = Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME)
        if day_only:
            all_favorites["favorites_day"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists,
                video_id__in=video_list,
                date_added__date=date_filter,
            ).count()
        elif years_only:
            all_favorites["favorites_year"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists,
                video_id__in=video_list,
                date_added__year=date_filter.year,
            ).count()
        else:
            all_favorites["favorites_since_created"] = PlaylistContent.objects.filter(
                playlist__in=favorites_playlists, video_id__in=video_list
            ).count()

        cache.set(cache_key, all_favorites, CACHE_EXPIRATION)

    return all_favorites


def get_days_videos_stats(
    video_list: List[Video], date_filter: date = date.today()
) -> str:
    """
    Get daily aggregated statistics data for a list of videos based on the specified date filter.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date, optional): The date filter to apply. Defaults to today's date.

    Returns:
        str: A JSON-encoded string containing the aggregated daily statistics data.
    """
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


def get_years_videos_stats(
    video_list: List[Video], date_filter: date = date.today()
) -> str:
    """
    Get yearly aggregated statistics data for a list of videos based on the specified date filter.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of video objects.
        date_filter (date, optional): The date filter to apply. Defaults to today's date.

    Returns:
        str: A JSON-encoded string containing the aggregated yearly statistics data.
    """
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


def get_videos_status_stats(video_list: List[Video]) -> str:
    """
    Get statistics for the status of videos in the given list.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of Video objects.

    Returns:
        str: JSON-encoded statistics for different video statuses.
    """
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


def get_playlists_status_stats(playlist_list: List[Playlist]) -> str:
    """
    Get statistics for the visibility statuses of playlists in the given list.

    Args:
        playlist_list (List[:class:`pod.playlist.models.Playlist`]): List of Playlist objects.

    Returns:
        str: JSON-encoded statistics for different playlist visibility statuses.
    """
    stats = {}
    visibility_list = list(playlist_list.values_list("visibility", flat=True))
    stats = Counter(visibility_list)
    return dumps(stats)


def total_time_videos(request: HttpRequest, video_list: List[Video] = None) -> str:
    """
    Get the total duration of videos in the specified list or for the user's available videos.

    Args:
        request (HttpRequest): The HTTP request object.
        video_list (List[:class:`pod.video.models.Video`], optional): List of Video objects. Defaults to None.

    Returns:
        str: The formatted total duration of videos in HH:MM:SS format.
    """
    if video_list:
        total_duration = video_list.aggregate(Sum("duration"))["duration__sum"]
    else:
        total_duration = get_available_videos(request).aggregate(Sum("duration"))[
            "duration__sum"
        ]
    return str(timedelta(seconds=total_duration)) if total_duration else "0"


def number_videos(request: HttpRequest, video_list: List[Video] = None) -> int:
    """
    Get the number of videos in the specified list or for the user's available videos.

    Args:
        request (HttpRequest): The HTTP request object.
        video_list (List[:class:`pod.video.models.Video`], optional): List of Video objects. Defaults to None.

    Returns:
        int: The number of videos.
    """
    if video_list:
        number_videos = video_list.count()
    else:
        number_videos = get_available_videos(request).count()
    return number_videos


def number_files(user: User) -> int:
    """
    Get the number of files in the user's home folder.

    Args:
        user (:class:`django.contrib.auth.models.User`): The User object.

    Returns:
        int: The number of files.
    """
    user_home_folder = get_object_or_404(UserFolder, name="home", owner=user)
    return len(user_home_folder.get_all_files())


def number_favorites(user: User) -> int:
    """
    Get the number of videos in the user's favorite playlist.

    Args:
        user (:class:`django.contrib.auth.models.User`): The User object.

    Returns:
        int: The number of videos in the favorite playlist.
    """
    favorites = get_favorite_playlist_for_user(user)
    return get_number_video_in_playlist(favorites)


def number_meetings(user: User) -> int:
    """
    Get the number of meetings owned by the user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The User object.

    Returns:
        int: The number of meetings.
    """
    return Meeting.objects.filter(owner=user).count()


def number_channels(request: HttpRequest, target: str = None) -> int:
    """
    Get the number of channels for the user or in total.

    Args:
        request (HttpRequest): The HTTP request object.
        target (str, optional): The target for counting channels. Defaults to None.

    Returns:
        int: The number of channels.
    """
    site = get_current_site(request)
    if target == "user":
        return request.user.owners_channels.all().filter(site=site).count()
    return Channel.objects.all().filter(site=site).distinct().count()


def get_channels_visibility_stats(channel_list: List[Channel]) -> str:
    """
    Get statistics for the visibility statuses of channels in the given list.

    Args:
        channel_list (List[:class:`pod.video.models.Channel`]): List of Channel objects.

    Returns:
        str: JSON-encoded statistics for different channel visibility statuses.
    """
    stats = {}
    number_channels = len(channel_list)

    visible_channels = channel_list.filter(visible=True).count()
    private_channels = number_channels - visible_channels

    stats["visible"] = visible_channels
    stats["private"] = private_channels
    return dumps(stats)


def get_most_common_type_discipline(video_list: List[Video]):
    """
    Get the most common video type and discipline from the given list of videos.

    Args:
        video_list (List[:class:`pod.video.models.Video`]): List of Video objects.

    Returns:
        Tuple[Type, Discipline]: The most common video type and discipline.
    """
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


def number_users() -> int:
    """
    Get the total number of users.

    Returns:
        int: The number of users.
    """
    return User.objects.all().distinct().count()


def number_themes(channel: Channel = None) -> int:
    """
    Get the number of themes for the specified channel or in total.

    Args:
        channel (:class:`pod.video.models.Channel`, optional): The Channel object. Defaults to None.

    Returns:
        int: The number of themes.
    """
    if channel:
        return Theme.objects.filter(channel=channel).distinct().count()
    else:
        return Theme.objects.all().distinct().count()
