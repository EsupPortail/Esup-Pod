"""Esup-Pod video utilities."""
from django.db.models.functions import Lower
import os
import re
import shutil
from math import ceil

from django.urls import reverse
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Q
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from .models import Video


DEBUG = getattr(settings, "DEBUG", True)

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/esup-pod.svg",
        "LOGO_PLAYER": "img/pod_favicon.svg",
        "LINK_PLAYER": "",
        "LINK_PLAYER_NAME": _("Home"),
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/pod_favicon.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)

DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")

USE_ESTABLISHMENT_FIELD = getattr(settings, "USE_ESTABLISHMENT_FIELD", False)

MANAGERS = getattr(settings, "MANAGERS", {})

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)
VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")

###############################################################
# EMAIL
###############################################################


def pagination_data(request_path, offset, limit, total_count):
    """Get next, previous url and info about max number of page and current page.

    :param request_path: str: current request path
    :param offset:       int: data offset
    :param limit:        int: data max number
    :param total_count:  int: total data count

    :return: Tuple[str]: next, previous url and current page info
    """
    next_url = previous_url = None
    pages_info = "0/0"
    # manage next previous url (Pagination)
    if offset + limit < total_count and limit <= total_count:
        next_url = "{}?limit={}&offset={}".format(request_path, limit, limit + offset)
    if offset - limit >= 0 and limit <= total_count:
        previous_url = "{}?limit={}&offset={}".format(request_path, limit, offset - limit)

    current_page = 1 if offset <= 0 else int((offset / limit)) + 1
    total = ceil(total_count / limit)
    pages_info = "{}/{}".format(current_page if total > 0 else 0, total)

    return next_url, previous_url, pages_info


def get_headband(channel, theme=None):
    """Get headband with priority to theme headband.

    :param channel: (Channel): channel
    :param theme: (Theme, optional): theme, Defaults to None.

    :return: dict: type(theme, channel) and headband path
    """
    result = {
        "type": "channel" if theme is None else "theme",
        "headband": None,
    }
    if theme is not None and theme.headband is not None:
        result["headband"] = theme.headband.file.url  # pragma: no cover
    elif theme is None and channel.headband is not None:
        result["headband"] = channel.headband.file.url  # pragma: no cover

    return result


def change_owner(video_id, new_owner):
    """Replace current video_id owner by new_owner."""
    if video_id is None:
        return False

    video = Video.objects.filter(pk=video_id).first()
    if video is None:
        return False
    video.owner = new_owner
    video.save()
    move_video_file(video, new_owner)
    return True


def move_video_file(video, new_owner):
    """Move video files in new_owner folder."""
    # overview and encoding video folder name
    encod_folder_pattern = "%04d" % video.id
    old_dest = os.path.join(os.path.dirname(video.video.path), encod_folder_pattern)
    new_dest = re.sub(r"\w{64}", new_owner.owner.hashkey, old_dest)

    # move video files folder contains(overview, format etc...)
    if not os.path.exists(new_dest) and os.path.exists(old_dest):
        new_dest = re.sub(encod_folder_pattern + "/?", "", new_dest)
        if not os.path.exists(new_dest):
            os.makedirs(new_dest)
        shutil.move(old_dest, new_dest)

    # update video overview path
    if bool(video.overview):
        video.overview = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video.overview.__str__()
        )

    # Update video playlist source file
    video_playlist_master = video.get_playlist_master()
    if video_playlist_master is not None:
        video_playlist_master.source_file.name = re.sub(
            r"\w{64}", new_owner.owner.hashkey, video_playlist_master.source_file.name
        )
        video_playlist_master.save()

    # update video path
    video_file_pattern = r"[\w-]+\.\w+"
    old_video_path = video.video.path
    new_video_path = re.sub(r"\w{64}", new_owner.owner.hashkey, old_video_path)
    video.video.name = new_video_path.split("media/")[1]
    if not os.path.exists(new_video_path) and os.path.exists(old_video_path):
        new_video_path = re.sub(video_file_pattern, "", new_video_path)
        shutil.move(old_video_path, new_video_path)
    video.save()


def get_videos(title, user_id, search=None, limit=12, offset=0):
    """Return videos filtered by GET parameters 'title' with limit and offset.

    Args:
        request (Request): Http Request

    Returns:
        list[dict]: videos found
    """
    videos = Video.objects.filter(owner__id=user_id).order_by("id")
    if search is not None:
        title = search

    if title is not None:
        videos = videos.filter(
            Q(title__icontains=title)
            | Q(title_fr__icontains=title)
            | Q(title_en__icontains=title)
        )

    count = videos.count()
    results = list(
        map(
            lambda v: {"id": v.id, "title": v.title, "thumbnail": v.get_thumbnail_url()},
            videos[offset : limit + offset],
        )
    )

    next_url, previous_url, page_infos = pagination_data(
        reverse("video:filter_videos", kwargs={"user_id": user_id}), offset, limit, count
    )

    response = {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "page_infos": page_infos,
        "results": results,
    }
    return JsonResponse(response, safe=False)


def sort_videos_list(videos_list, sort_field, sort_direction=""):
    """Return videos list sorted by sort_field.

    Sorted by specific column name and ascending or descending direction
    """
    if sort_field and sort_field in {
        "category",
        "channel",
        "cursus",
        "date_added",
        "date_evt",
        "discipline",
        "duration",
        "id",
        "is_360",
        "is_restricted",
        "is_video",
        "licence",
        "main_lang",
        "owner",
        "sites",
        "theme",
        "title",
        "title_en",
        "title_fr",
        "type",
        "viewcount",
        "rank",
    }:
        if sort_field in {"title", "title_fr", "title_en"}:
            sort_field = Lower(sort_field)
            if not sort_direction:
                sort_field = sort_field.desc()

        elif not sort_direction:
            sort_field = "-" + sort_field
        videos_list = videos_list.order_by(sort_field)

    return videos_list.distinct()


def get_id_from_request(request, key):
    """Get the value of a specified key from the request object."""
    if request.method == "POST" and request.POST.get(key):
        return request.POST.get(key)
    elif request.method == "GET" and request.GET.get(key):
        return request.GET.get(key)
    return None


def get_video_data(video):
    """Get a dictionary containing data from a video object."""
    return {
        "slug": video.slug,
        "title": video.title,
        "duration": video.duration_in_time,
        "thumbnail": video.get_thumbnail_card(),
        "is_video": video.is_video,
        "has_password": bool(video.password),
        "is_restricted": video.is_restricted,
        "has_chapter": video.chapter_set.all().count() > 0,
        "is_draft": video.is_draft,
    }


def get_storage_path_video(instance, filename):
    """Get the video storage path.

    Instance needs to implement owner
    """
    fname, dot, extension = filename.rpartition(".")
    try:
        fname.index("/")
        return os.path.join(
            VIDEOS_DIR,
            instance.owner.owner.hashkey,
            "%s/%s.%s"
            % (
                os.path.dirname(fname),
                slugify(os.path.basename(fname)),
                extension,
            ),
        )
    except ValueError:
        return os.path.join(
            VIDEOS_DIR,
            instance.owner.owner.hashkey,
            "%s.%s" % (slugify(fname), extension),
        )
