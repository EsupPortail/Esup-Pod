from django.shortcuts import render
from django.db.models import Min
from datetime import date
from pod.stats.utils import get_all_videos_stats
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


def get_videos(target, slug=None):
    title = _("Pod video viewing statistics")
    available_videos = get_available_videos()
    videos = []
    if target == "videos":
        if slug:
            try:
                video_founded = Video.objects.get(slug=slug)
                videos.append(video_founded)
                title = (
                    _("Video viewing statistics for %s") % video_founded.title.capitalize()
                )
            except Video.DoesNotExist:
                ...  # TODO redirection
        else:
            videos = available_videos
    # elif target.lower() == "channel":
    #     title = _("Video viewing statistics for the channel %s") % p_slug
    #     videos = available_videos.filter(channel__slug__istartswith=p_slug)

    # elif target.lower() == "theme" and p_slug_t:
    #     title = _("Video viewing statistics for the theme %s") % p_slug_t
    #     videos = available_videos.filter(theme__slug__istartswith=p_slug_t)

    return (videos, title)


def view_stats_if_authenticated(user):
    if user.is_authenticated and VIEW_STATS_AUTH:
        return False
    return True


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def video_stats_view(request, video=None):
    target = "videos"
    videos, title = get_videos(target=target, slug=video)

    error_message = "The following %(target)s does not exist or contain any videos: %(video)s"

    if request.method == "GET":
        if video and videos:
            return manage_access_rights_stats_video(request, videos[0], title)
        elif not videos:
            return HttpResponseNotFound(_("The following video does not exist: %s") % video)

    if (
        request.method == "POST"
        and target == "video"
        and request.POST.get("password") == videos[0].password
    ) or (request.method == "GET" and not video and videos):
        return render(request, "videos/video_stats_view.html", {"title": title})
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()
        data = [
            {
                "title": v.title,
                "slug": v.slug,
                **get_all_videos_stats(v.id, date_filter),
            } for v in videos
        ]

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
            "videos/video_stats_view.html",
            {"form": form, "title": page_title},
        )
    elif (
        (not has_rights and video_access_ok and not is_password_protected)
        or (video_access_ok and not is_password_protected)
        or has_rights
    ):
        return render(
            request,
            "videos/video_stats_view.html",
            {"title": page_title, "slug": video.slug}
        )
    return HttpResponseNotFound(_("You do not have access rights to this video: %s" % video.slug))


def to_do():
    ...
