import json
from datetime import date
from dateutil.parser import parse
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _

from pod.playlist.utils import (
    get_all_playlists,
    get_favorite_playlist_for_user,
    get_playlist,
    get_video_list_for_playlist,
)
from pod.stats.utils import (
    get_channels_visibility_stats,
    get_most_common_type_discipline,
    get_playlists_status_stats,
    get_videos_stats,
    get_videos_status_stats,
)
from pod.video.context_processors import get_available_videos
from pod.video.forms import VideoPasswordForm
from pod.video.models import Channel, Theme, Video
from pod.video.views import get_video_access

VIEW_STATS_AUTH = getattr(settings, "VIEW_STATS_AUTH", False)


def view_stats_if_authenticated(user):
    return user.is_authenticated and VIEW_STATS_AUTH


STATS_VIEWS = {
    "videos": {
        "filter_func": lambda kwargs: Video.objects.filter(slug=kwargs.get("video_slug"))
        if kwargs.get("video_slug")
        else kwargs["available_videos"],
        "title_func": lambda kwargs: _("Video statistics: %s")
        % kwargs["video_founded"].title.capitalize()
        if kwargs["video_founded"]
        else _("Site video statistics"),
    },
    "channel": {
        "filter_func": lambda kwargs: Video.objects.filter(
            channel=kwargs["channel_obj"], theme=kwargs["theme_obj"]
        )
        if kwargs.get("theme_obj")
        else Video.objects.filter(channel=kwargs["channel_obj"]),
        "title_func": lambda kwargs: _("Video statistics for the theme %s")
        % kwargs["theme_obj"].title
        if kwargs.get("theme_obj")
        else _("Video statistics for the channel %s") % kwargs["channel_obj"].title
        if kwargs["channel_obj"]
        else _("Statistics for channels"),
    },
    "user": {
        "filter_func": lambda kwargs: Video.objects.filter(owner=kwargs["user"]),
        "title_func": lambda kwargs: _("Statistics for user %s") % kwargs["user"],
    },
    "general": {
        "filter_func": lambda kwargs: kwargs["available_videos"],
        "title_func": lambda kwargs: _("Site statistics"),
    },
    "playlist": {
        "filter_func": lambda kwargs: Video.objects.filter(
            playlistcontent__playlist=kwargs["playlist_obj"]
        ),
        "title_func": lambda kwargs: _("Statistics for the playlist %s")
        % kwargs["playlist_obj"].name
        if kwargs["playlist_obj"]
        else _("Statistics for playlists"),
    },
}


def get_videos(
    request, target: str, video_slug=None, channel=None, theme=None, playlist=None
):
    title = _("Video statistics")
    available_videos = get_available_videos()
    videos = []

    if target.lower() in STATS_VIEWS:
        config = STATS_VIEWS[target.lower()]
        filter_args = {
            "video_slug": video_slug,
            "channel": channel,
            "theme": theme,
            "playlist": playlist,
            "available_videos": available_videos,
            "user": request.user if target.lower() == "user" else None,
            "channel_obj": get_object_or_404(Channel, slug=channel) if channel else None,
            "theme_obj": get_object_or_404(Theme, slug=theme) if theme else None,
            "video_founded": Video.objects.filter(slug=video_slug).first()
            if video_slug
            else None,
            "playlist_obj": get_playlist(playlist) if playlist else None,
        }
        videos = config["filter_func"](filter_args)
        title = config["title_func"](filter_args)

    return videos, title


def manage_post_request(request, videos, video=None):
    date_filter = request.POST.get("periode", date.today())
    if isinstance(date_filter, str):
        date_filter = parse(date_filter).date()
    if video:  # For one video
        data = get_videos_stats(videos, date_filter)
    else:  # For some videos
        data = get_videos_stats(videos, date_filter, mode="year")
    return JsonResponse(data, safe=False)


@user_passes_test(view_stats_if_authenticated)
def video_stats_view(request, video=None):
    target = "videos"
    videos, title = get_videos(request=request, target=target, video_slug=video)

    if not videos:
        return HttpResponseNotFound(_("The following video does not exist: %s") % video)

    if request.method == "GET":
        if video and videos:
            return manage_access_rights_stats_video(request, videos[0], title)

        status_datas_json = get_videos_status_stats(videos)
        status_datas = json.loads(status_datas_json)
        status_datas.pop("draft", None)
        prefered_type, prefered_discipline = get_most_common_type_discipline(videos)

        return render(
            request,
            "stats/video-stats-view.html",
            {
                "title": title,
                "videos": videos,
                "status_datas": json.dumps(status_datas),
                "prefered_type": prefered_type,
                "prefered_discipline": prefered_discipline,
            },
        )
    if request.method == "POST":
        return manage_post_request(request, videos, video)


def manage_access_rights_stats_video(request, video, page_title):
    video_access_ok = get_video_access(request, video, slug_private=None)
    is_password_protected = video.password is not None and video.password != ""
    has_rights = (
        request.user == video.owner
        or request.user.is_superuser
        or request.user.has_perm("video.change_viewcount")
        or request.user in video.additional_owners.all()
    )
    if not has_rights and is_password_protected:
        form = VideoPasswordForm()
        return render(
            request,
            "stats/video-stats-view.html",
            {"form": form, "title": page_title},
        )
    elif (
        (not has_rights and video_access_ok and not is_password_protected)
        or (video_access_ok and not is_password_protected)
        or has_rights
    ):
        return render(
            request,
            "stats/video-stats-view.html",
            {
                "title": page_title,
                "video": video,
                "slug": video.slug,
            },
        )
    return HttpResponseNotFound(
        _("You do not have access rights to this video: %s" % video.slug)
    )


def to_do():
    ...


@user_passes_test(view_stats_if_authenticated)
def channel_stats_view(request, channel=None, theme=None):
    target = "channel"
    videos, title = get_videos(
        request=request, target=target, channel=channel, theme=theme
    )

    if request.method == "GET":
        if channel:
            status_datas = get_videos_status_stats(videos)
            return render(
                request,
                "stats/channel-stats-view.html",
                {
                    "title": title,
                    "channel": channel,
                    "status_datas": status_datas,
                    "videos": videos,
                    "date": date.today(),
                },
            )
        else:
            site = get_current_site(request)
            channels = Channel.objects.all().filter(site=site).distinct()
            visibility_datas = get_channels_visibility_stats(channels)
            return render(
                request,
                "stats/channel-stats-view.html",
                {
                    "title": title,
                    "visibility_datas": visibility_datas,
                },
            )

    elif request.method == "POST":
        return manage_post_request(request, videos)


@user_passes_test(view_stats_if_authenticated)
def user_stats_view(request):
    target = "user"
    videos, title = get_videos(request=request, target=target)

    if request.method == "GET":
        status_datas = get_videos_status_stats(videos)
        prefered_type, prefered_discipline = get_most_common_type_discipline(
            get_video_list_for_playlist(get_favorite_playlist_for_user(request.user))
        )
        return render(
            request,
            "stats/user-stats-view.html",
            {
                "title": title,
                "videos": videos,
                "status_datas": status_datas,
                "prefered_type": prefered_type,
                "prefered_discipline": prefered_discipline,
            },
        )
    elif request.method == "POST":
        return manage_post_request(request, videos)


@user_passes_test(view_stats_if_authenticated)
def general_stats_view(request):
    target = "general"
    videos, title = get_videos(request=request, target=target)

    if request.method == "GET":
        status_datas_json = get_videos_status_stats(videos)
        status_datas = json.loads(status_datas_json)
        status_datas.pop("draft", None)
        prefered_type, prefered_discipline = get_most_common_type_discipline(videos)
        return render(
            request,
            "stats/general-stats-view.html",
            {
                "title": title,
                "videos": videos,
                "status_datas": json.dumps(status_datas),
                "prefered_type": prefered_type,
                "prefered_discipline": prefered_discipline,
            },
        )
    elif request.method == "POST":
        return manage_post_request(request, videos)


@user_passes_test(view_stats_if_authenticated)
def playlist_stats_view(request, playlist=None):
    target = "playlist"
    videos, title = get_videos(request=request, target=target, playlist=playlist)

    if request.method == "GET":
        if playlist:
            status_datas = get_videos_status_stats(videos)
            prefered_type, prefered_discipline = get_most_common_type_discipline(videos)
            playlist = get_playlist(playlist)
            return render(
                request,
                "stats/playlist-stats-view.html",
                {
                    "title": title,
                    "videos": videos,
                    "status_datas": status_datas,
                    "prefered_type": prefered_type,
                    "prefered_discipline": prefered_discipline,
                    "playlist": playlist,
                },
            )
        else:
            playlists = get_all_playlists()
            status_datas = get_playlists_status_stats(playlists)
            return render(
                request,
                "stats/playlist-stats-view.html",
                {
                    "title": title,
                    "playlists": playlists,
                    "status_datas": status_datas,
                },
            )
    elif request.method == "POST":
        return manage_post_request(request, videos)
