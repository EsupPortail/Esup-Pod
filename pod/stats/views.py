import json
from django.shortcuts import render
from datetime import date
from pod.playlist.models import Playlist
from pod.playlist.utils import get_favorite_playlist_for_user, get_video_list_for_playlist
from pod.stats.utils import (
    get_most_common_type_discipline,
    get_videos_stats,
    get_videos_status_stats,
)
from pod.video.context_processors import get_available_videos
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseNotFound
from dateutil.parser import parse
from django.http import JsonResponse
from pod.video.forms import VideoPasswordForm
from pod.video.models import Video
from pod.video.views import get_video_access
from django.shortcuts import redirect

VIEW_STATS_AUTH = getattr(settings, "VIEW_STATS_AUTH", False)


def get_videos(request, target: str, slug=None, channel=None, theme=None, playlist=None):
    title = _("Video statistics")
    available_videos = get_available_videos()
    videos = []
    if target.lower() == "videos":
        if slug:
            try:
                video_founded = Video.objects.get(slug=slug)
                videos.append(video_founded)
                title = _("Video statistics for %s") % video_founded.title.capitalize()
            except Video.DoesNotExist:
                return redirect(request.META["HTTP_REFERER"])
        else:
            videos = available_videos
    elif target.lower() == "channel":
        if channel and theme:
            title = _("Video statistics for the theme %s") % theme.capitalize()
            videos = Video.objects.filter(theme__slug__istartswith=theme)
        elif channel and not theme:
            title = _("Video statistics for the channel %s") % slug.capitalize()
            videos = Video.objects.filter(channel__slug__istartswith=slug)
        else:
            title = _("Statistics for channels")
    elif target.lower() == "user":
        title = _("Statistics for user %s") % request.user
        videos = Video.objects.filter(owner=request.user)
    elif target.lower() == "general":
        title = _("Site statistics")
        videos = available_videos
    elif target.lower() == "playlist":
        if playlist:
            playlist = Playlist.objects.get(slug=playlist)
            title = _("Statistics for the playlist %s") % playlist.name
            videos = Video.objects.filter(playlistcontent__playlist=playlist)
        else:
            title = _("Statistics for playlists")
    return (videos, title)


def view_stats_if_authenticated(user):
    if user.is_authenticated and VIEW_STATS_AUTH:
        return False
    return True


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def video_stats_view(request, video=None):
    target = "videos"
    videos, title = get_videos(request=request, target=target, slug=video)

    if request.method == "GET":
        if video and videos:
            return manage_access_rights_stats_video(request, videos[0], title)
        elif not videos:
            return HttpResponseNotFound(
                _("The following video does not exist: %s") % video
            )

    if request.method == "GET" and not video and videos:
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
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        if video:  # For one video
            data = get_videos_stats(videos, date_filter)
        else:  # For some videos
            data = get_videos_stats(videos, date_filter, mode="year")
        return JsonResponse(data, safe=False)


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


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def channel_stats_view(request, channel=None, theme=None):
    target = "channel"
    videos, title = get_videos(request=request, target=target, slug=channel, theme=theme)

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
                    "date": date.today(),
                },
            )
        else:
            return render(
                request,
                "stats/channel-stats-view.html",
                {
                    "title": title,
                },
            )

    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = get_videos_stats(videos, date_filter, mode="year")
        return JsonResponse(data, safe=False)


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
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
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = get_videos_stats(videos, date_filter, mode="year")
        return JsonResponse(data, safe=False)


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
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
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = get_videos_stats(videos, date_filter, mode="year")
        return JsonResponse(data, safe=False)


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def playlist_stats_view(request, playlist=None):
    target = "playlist"
    videos, title = get_videos(request=request, target=target, playlist=playlist)
    if request.method == "GET":
        if playlist:
            status_datas = get_videos_status_stats(videos)
            prefered_type, prefered_discipline = get_most_common_type_discipline(videos)
            playlist = Playlist.objects.get(slug=playlist)
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
            return render(
                request,
                "stats/playlist-stats-view.html",
                {
                    "title": title,
                    # "status_datas": status_datas,
                    # "prefered_type": prefered_type,
                    # "prefered_discipline": prefered_discipline,
                    # "playlist": playlist,
                },
            )
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = get_videos_stats(videos, date_filter, mode="year")
        return JsonResponse(data, safe=False)
