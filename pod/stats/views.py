import json
from django.shortcuts import render
from django.db.models import Min
from datetime import date
from pod.stats.utils import get_videos_stats, get_videos_status_stats
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

VIEW_STATS_AUTH = getattr(settings, "VIEW_STATS_AUTH", False)


def get_videos(target: str, slug=None, theme=None):
    title = _("Pod statistics")
    available_videos = get_available_videos()
    videos = []
    if target.lower() == "videos":
        if slug:
            try:
                video_founded = Video.objects.get(slug=slug)
                videos.append(video_founded)
                title = _("Video statistics for %s") % video_founded.title.capitalize()
            except Video.DoesNotExist:
                ...  # TODO redirection
        else:
            videos = available_videos
    elif target.lower() == "channel":
        if theme:
            title = _("Video statistics for the theme %s") % theme.capitalize()
            videos = Video.objects.filter(theme__slug__istartswith=theme)
        else:
            title = _("Video statistics for the channel %s") % slug.capitalize()
            videos = Video.objects.filter(channel__slug__istartswith=slug)

    return (videos, title)


def view_stats_if_authenticated(user):
    if user.is_authenticated and VIEW_STATS_AUTH:
        return False
    return True


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def video_stats_view(request, video=None):
    target = "videos"
    videos, title = get_videos(target=target, slug=video)

    if request.method == "GET":
        if video and videos:
            return manage_access_rights_stats_video(request, videos[0], title)
        elif not videos:
            return HttpResponseNotFound(_("The following video does not exist: %s") % video)

    if request.method == "GET" and not video and videos:
        return render(request, "stats/video-stats-view.html", {"title": title})
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = get_videos_stats(videos, date_filter)

        min_date = get_available_videos().aggregate(
            Min("date_added"))["date_added__min"].date()
        data.append({"min_date": min_date})

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
            {"title": page_title, "slug": video.slug}
        )
    return HttpResponseNotFound(_("You do not have access rights to this video: %s" % video.slug))


def to_do():
    ...


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def channel_stats_view(request, channel=None, theme=None):
    target = "channel"
    videos, title = get_videos(target=target, slug=channel, theme=theme)

    if request.method == "GET" and channel and videos:
        status_percentages = get_videos_status_stats(videos)
        return render(
            request,
            "stats/channel-stats-view.html",
            {
                "title": title,
                "channel": channel,
                "status_datas": json.dumps(status_percentages),
                "date": date.today()
            }
        )
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()

        data = get_videos_stats(videos, date_filter)
        min_date = get_available_videos().aggregate(
            Min("date_added"))["date_added__min"].date()
        data.append({"min_date": min_date})

        return JsonResponse(data, safe=False)
