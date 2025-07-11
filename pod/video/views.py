"""Esup-Pod videos views."""

from concurrent import futures
import os

from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count, F, Q, Case, When, Value, BooleanField
from django.db.models.functions import Concat
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseNotFound
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.http import QueryDict, Http404
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils.translation import ngettext
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Min


# from django.contrib.auth.hashers import check_password

from dateutil.parser import parse
from pod.main.utils import is_ajax, dismiss_stored_messages, get_max_code_lvl_messages
from pod.main.context_processors import WEBTV_MODE
from pod.main.models import AdditionalChannelTab
from pod.main.views import in_maintenance
from pod.main.decorators import ajax_required, ajax_login_required, admin_required
from pod.authentication.utils import get_owners as auth_get_owners
from pod.playlist.apps import FAVORITE_PLAYLIST_NAME
from pod.playlist.models import Playlist, PlaylistContent
from pod.playlist.utils import (
    get_video_list_for_playlist,
    playlist_can_be_displayed,
    user_can_see_playlist_video,
)
from pod.video.utils import get_videos as video_get_videos
from pod.video.models import Video
from pod.video.models import Type
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import AdvancedNotes, NoteComments, NOTES_STATUS
from pod.video.models import ViewCount, VideoVersion
from pod.video.models import Comment, Vote, Category
from pod.video.models import get_transcription_choices
from pod.video.models import UserMarkerTime, VideoAccessToken
from pod.video.forms import VideoForm, VideoVersionForm
from pod.video.forms import ChannelForm
from pod.video.forms import FrontThemeForm
from pod.video.forms import VideoPasswordForm
from pod.video.forms import VideoDeleteForm
from pod.video.forms import AdvancedNotesForm, NoteCommentsForm
from pod.video.rest_views import ChannelSerializer

from .utils import (
    pagination_data,
    get_headband,
    change_owner,
    get_id_from_request,
)
from .context_processors import get_available_videos
from .utils import sort_videos_list

from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
import json
import re
import pandas
import uuid
from datetime import date
from chunked_upload.models import ChunkedUpload
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from itertools import chain

from django.db import IntegrityError
from django.db.models import QuerySet
from django.db import transaction

RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY", False
)
__THEME_ACTION__ = ["new", "modify", "delete", "save"]
__NOTE_ACTION__ = ["get", "save", "remove", "form", "download"]

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "DESC_SITE": "The purpose of Esup-Pod is to facilitate the provision of video and\
        thereby encourage its use in teaching and research.",
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
TEMPLATE_VISIBLE_SETTINGS["DESC_SITE"] = (
    TEMPLATE_VISIBLE_SETTINGS["DESC_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("DESC_SITE"))
    else "The purpose of Esup-Pod is to facilitate the provision of video and\
 thereby encourage its use in teaching and research."
)

VIDEO_MAX_UPLOAD_SIZE = getattr(settings, "VIDEO_MAX_UPLOAD_SIZE", 1)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)

CURSUS_CODES = getattr(
    settings,
    "CURSUS_CODES",
    (
        ("0", _("None / All")),
        ("L", _("Bachelor’s Degree")),
        ("M", _("Master’s Degree")),
        ("D", _("Doctorate")),
        ("1", _("Other")),
    ),
)

VIEW_STATS_AUTH = getattr(settings, "VIEW_STATS_AUTH", False)
ACTIVE_VIDEO_COMMENT = getattr(settings, "ACTIVE_VIDEO_COMMENT", False)
USER_VIDEO_CATEGORY = getattr(settings, "USER_VIDEO_CATEGORY", False)
DEFAULT_TYPE_ID = getattr(settings, "DEFAULT_TYPE_ID", 1)
ORGANIZE_BY_THEME = getattr(settings, "ORGANIZE_BY_THEME", False)
HIDE_USER_FILTER = getattr(settings, "HIDE_USER_FILTER", False)
USE_TRANSCRIPTION = getattr(settings, "USE_TRANSCRIPTION", False)
USE_OBSOLESCENCE = getattr(settings, "USE_OBSOLESCENCE", False)

if USE_TRANSCRIPTION:
    from ..video_encode_transcript import transcript

    TRANSCRIPT_VIDEO = getattr(settings, "TRANSCRIPT_VIDEO", "start_transcript")

CHANNELS_PER_BATCH = getattr(settings, "CHANNELS_PER_BATCH", 10)


# ############################################################################
# CHANNEL
# ############################################################################


def get_theme_children_as_list(channel: Channel, theme_children: QuerySet) -> list:
    """Get theme children as a list, and not a Queryset.

    Args:
        channel (Channel): current channel
        theme_children (QuerySet): QuerySet of children in the theme
    Returns:
        list: list of children in the theme, with the right number of videos
    """
    # List of children in the theme
    children = list()
    for child in theme_children:
        if child is not None:
            # Get a flat list of all theme children.
            list_theme = child.get_all_children_flat()
            # Videos for each child theme
            videos_list = get_available_videos().filter(
                channel=channel, theme__in=list_theme
            )
            child.video_count = videos_list.count()
            child_serializable = {
                "slug": child.slug,
                "title": child.title,
                "video_count": child.video_count,
            }
            children.append(child_serializable)
    return children


def _regroup_videos_by_theme(  # noqa: C901
    request, videos, page, full_path, channel, theme=None
):
    """Regroup videos by theme.

    Args:
        request (Request): current HTTP Request
        videos (List[Video]): list of video filter by channel
        page (int): page number
        full_path (str): URL full path
        channel (Channel): current channel
        theme (Theme, optional): current theme. Defaults to None.
    Returns:
        JsonResponse for themes in Ajax, or HttpResponse for other cases (videos).
    """
    target = request.GET.get("target", "").lower()
    limit = int(request.GET.get("limit", 12))
    offset = int(request.GET.get("offset", 0))
    theme_children = None
    parent_title = ""
    response = {}

    if target in ("", "themes"):
        theme_children = Theme.objects.filter(parentId=theme, channel=channel)
        videos = videos.filter(theme=theme, channel=channel).distinct()

        if theme is not None and theme.parentId is not None:
            parent_title = theme.parentId.title
        elif theme is not None and theme.parentId is None:
            parent_title = channel.title

    if target in ("", "videos"):
        videos = videos.filter(theme=theme, channel=channel).distinct()
        response["next_videos"], *_ = pagination_data(
            request.path, offset, limit, videos.count()
        )
        count = videos.count()
        videos = videos[offset : limit + offset]
        response = {
            **response,
            "videos": list(videos),
            "count_videos": count,
            "has_more_videos": (offset + limit) < count,
        }

    if theme_children is not None:
        count_themes = theme_children.count()
        has_more_themes = (offset + limit) < count_themes
        # Default value for each child theme
        theme_children = theme_children.annotate(video_count=Value(0))
        # List of children in the theme
        children = get_theme_children_as_list(channel, theme_children)
        # Do not send all themes
        children = children[offset : limit + offset]
        next_url, previous_url, theme_pages_info = pagination_data(
            request.path, offset, limit, count_themes
        )
        response = {
            **response,
            "next": next_url,
            "previous": previous_url,
            "has_more_themes": has_more_themes,
            "count_themes": count_themes,
            "theme_children": children,
            "pages_info": theme_pages_info,
        }
    title = channel.title if theme is None else theme.title
    description = channel.description if theme is None else theme.description
    headband = get_headband(channel, theme).get("headband", None)
    response = {
        **response,
        "parent_title": parent_title,
        "title": title,
        "description": description,
        "headband": headband,
    }
    """
    # Old source code.
    # No need now. Keep it, for historical purposes, until we've verified that the new code works in all cases.
    videos = list(
            map(
                lambda v: {
                    **get_video_data(v),
                    "is_editable": v.is_editable(request.user),
                },
                videos,
            )
        )
    response["videos"] = videos
    """
    if is_ajax(request):
        if target == "themes":
            # No change to the old system, with data in JSON format
            return JsonResponse(response, safe=False)
        else:
            # New system, with data in HTML format
            if not videos:
                # No content
                return HttpResponse(status=204)
            else:
                # Content with videos
                videos = paginator(videos, page)
            return render(
                request,
                "videos/video_list.html",
                {
                    "videos": videos,
                    "theme": theme,
                    "channel": channel,
                    "full_path": full_path,
                },
            )

    return render(
        request,
        "channel/channel.html",
        {
            **response,
            "theme": theme,
            "channel": channel,
            "organize_theme": True,
        },
    )


def paginator(videos_list, page):
    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)
    return videos


def channel(request, slug_c, slug_t=None):
    channel = get_object_or_404(Channel, slug=slug_c, site=get_current_site(request))
    videos_list = get_available_videos().filter(channel=channel)
    videos_list = sort_videos_list(videos_list, "date_added", "on")
    channel.video_count = videos_list.count()

    theme = None
    if slug_t:
        theme = get_object_or_404(Theme, channel=channel, slug=slug_t)
        list_theme = theme.get_all_children_flat()
        videos_list = videos_list.filter(theme__in=list_theme)

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )
    videos = paginator(videos_list, page)

    if ORGANIZE_BY_THEME:
        # Specific case
        return _regroup_videos_by_theme(
            request, videos_list, page, full_path, channel, theme
        )

    if is_ajax(request):
        return render(
            request,
            "videos/video_list.html",
            {
                "channel": channel,
                "videos": videos,
                "theme": theme,
                "full_path": full_path,
            },
        )
    return render(
        request,
        "channel/channel.html",
        {
            "channel": channel,
            "videos": videos,
            "theme": theme,
            "full_path": full_path,
        },
    )


@login_required(redirect_field_name="referrer")
def my_channels(request):
    site = get_current_site(request)
    channels = (
        request.user.owners_channels.all()
        .filter(site=site)
        .annotate(video_count=Count("video", distinct=True))
    )
    return render(
        request,
        "channel/my_channels.html",
        {"channels": channels, "page_title": _("My channels")},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def channel_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug, site=get_current_site(request))
    if request.user not in channel.owners.all() and not (
        request.user.is_superuser or request.user.has_perm("video.change_channel")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this channel."))
        raise PermissionDenied
    channel_form = ChannelForm(
        instance=channel,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
    )
    if request.POST:
        channel_form = ChannelForm(
            request.POST,
            instance=channel,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
        )
        if channel_form.is_valid():
            channel = channel_form.save()
            messages.add_message(
                request, messages.INFO, _("The changes have been saved.")
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    return render(
        request,
        "channel/channel_edit.html",
        {
            "form": channel_form,
            "page_title": _("Editing the channel “%s”") % channel.title,
        },
    )


# ############################################################################
# THEME EDIT
# ############################################################################


@csrf_protect
@login_required(redirect_field_name="referrer")
def theme_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug, site=get_current_site(request))
    if request.user not in channel.owners.all() and not (
        request.user.is_superuser or request.user.has_perm("video.change_theme")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this channel."))
        raise PermissionDenied

    if is_ajax(request):
        if request.POST["action"] in __THEME_ACTION__:
            return eval("theme_edit_{0}(request, channel)".format(request.POST["action"]))

    form_theme = FrontThemeForm(initial={"channel": channel})
    return render(
        request,
        "channel/theme_edit.html",
        {"channel": channel, "form_theme": form_theme},
    )


def theme_edit_new(request, channel):
    form_theme = FrontThemeForm(initial={"channel": channel})
    return render(
        request,
        "channel/form_theme.html",
        {"form_theme": form_theme, "channel": channel},
    )


def theme_edit_modify(request, channel):
    theme = get_object_or_404(Theme, id=request.POST["id"])
    form_theme = FrontThemeForm(instance=theme)
    return render(
        request,
        "channel/form_theme.html",
        {"form_theme": form_theme, "channel": channel},
    )


def theme_edit_delete(request, channel):
    theme = get_object_or_404(Theme, id=request.POST["id"])
    theme.delete()
    rendered = render_to_string(
        "channel/list_theme.html",
        {"list_theme": channel.themes.all(), "channel": channel},
        request,
    )
    list_element = {"list_element": rendered}
    data = json.dumps(list_element)
    return HttpResponse(data, content_type="application/json")


def theme_edit_save(request, channel):
    """Save theme edition."""
    form_theme = None

    if request.POST.get("theme_id") and request.POST.get("theme_id") != "None":
        theme = get_object_or_404(Theme, id=request.POST["theme_id"])
        form_theme = FrontThemeForm(request.POST, instance=theme)
    else:
        form_theme = FrontThemeForm(request.POST)

    if form_theme.is_valid():
        form_theme.save()
        rendered = render_to_string(
            "channel/list_theme.html",
            {"list_theme": channel.themes.all(), "channel": channel},
            request,
        )
        list_element = {"list_element": rendered}
        data = json.dumps(list_element)
        return HttpResponse(data, content_type="application/json")
    else:
        rendered = render_to_string(
            "channel/form_theme.html",
            {"form_theme": form_theme, "channel": channel},
            request,
        )
        some_data_to_dump = {
            "errors": "%s" % _("Please correct errors"),
            "form": rendered,
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")


# ############################################################################
# VIDEOS
# ############################################################################


@login_required(redirect_field_name="referrer")
def dashboard(request):
    """
    Render the logged user's dashboard: videos list/bulk update's interface.

    Args:
        request (Request): current HTTP Request.

    Returns:
        Render of global views with updated filtered and sorted videos, categories,
         display_mode, etc...
    """
    data_context = {}
    videos_list = get_videos_for_owner(request)

    if USER_VIDEO_CATEGORY:
        categories = Category.objects.prefetch_related("video").filter(owner=request.user)
        if len(request.GET.getlist("categories")):
            categories_checked = request.GET.getlist("categories")
            categories_videos = categories.filter(
                slug__in=categories_checked
            ).values_list("video", flat=True)
            videos_list = videos_list.filter(pk__in=categories_videos)

        data_context["categories"] = categories
        data_context["all_categories_videos"] = get_json_videos_categories(request)

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    filtered_videos_list = get_filtered_videos_list(request, videos_list)
    sort_field = request.GET.get("sort") if request.GET.get("sort") else "date_added"
    sort_direction = request.GET.get("sort_direction")
    sorted_videos_list = sort_videos_list(
        filtered_videos_list, sort_field, sort_direction
    )
    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))
    owner_filter = owner_is_searchable(request.user)

    count_videos = len(sorted_videos_list)

    paginator = Paginator(sorted_videos_list, 12)
    videos = get_paginated_videos(paginator, page)

    videos_list_templates = {
        "grid": "videos/video_list_grid_selectable.html",
        "list": "videos/video_list_table_selectable.html",
    }

    display_mode = (
        request.GET.get("display_mode")
        if request.GET.get("display_mode")
        and request.GET.get("display_mode") in videos_list_templates.keys()
        else "grid"
    )
    template = videos_list_templates[display_mode]

    if is_ajax(request):
        return render(
            request,
            template,
            {
                "videos": videos,
                "full_path": full_path,
                "count_videos": count_videos,
                "cursus_codes": CURSUS_CODES,
                "owner_filter": owner_filter,
            },
        )

    default_owner = request.user.pk
    form = VideoForm(
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": default_owner},
    )
    # Remove fields we don't want to be bulk-modified
    for unwanted in ["title", "video"]:
        del form.fields[unwanted]

    data_context["form"] = form
    data_context["fieldsets_dashboard"] = [
        "channel_option",
        "access_restrictions",
        "advanced_options",
    ]
    data_context["use_category"] = USER_VIDEO_CATEGORY
    data_context["use_obsolescence"] = USE_OBSOLESCENCE
    data_context["use_transcription"] = USE_TRANSCRIPTION
    data_context["videos"] = videos
    data_context["count_videos"] = count_videos
    data_context["types"] = request.GET.getlist("type")
    data_context["owners"] = request.GET.getlist("owner")
    data_context["disciplines"] = request.GET.getlist("discipline")
    data_context["tags_slug"] = request.GET.getlist("tag")
    data_context["cursus_selected"] = request.GET.getlist("cursus")
    data_context["cursus_codes"] = CURSUS_CODES
    data_context["full_path"] = full_path
    data_context["owners"] = request.GET.getlist("owner")
    data_context["ownersInstances"] = ownersInstances
    data_context["sort_field"] = sort_field
    data_context["sort_direction"] = request.GET.get("sort_direction")
    data_context["owner_filter"] = owner_filter
    data_context["display_mode"] = display_mode
    data_context["video_list_template"] = template
    data_context["page_title"] = _("Dashboard")
    data_context["listTheme"] = json.dumps(get_list_theme_in_form(form))

    return render(request, "videos/dashboard.html", data_context)


@login_required(redirect_field_name="referrer")
def bulk_update(request):
    """
    Perform bulk update for selected videos.

    Args:
        request (Request): current HTTP Request.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response of bulk update.
    """
    if request.method == "POST":
        status = 200
        # Get post parameters
        update_action = request.POST.get("update_action")
        selected_videos = json.loads(request.POST.get("selected_videos"))
        videos_list = Video.objects.filter(slug__in=selected_videos)

        # Init return json object
        result = {
            "message": "",
            "fields_errors": [],
            "updated_videos": [],
        }

        if videos_list.exists():
            counter = 0
            if update_action == "fields":
                # Bulk update fields
                update_fields = json.loads(request.POST.get("update_fields"))
                (result["updated_videos"], fields_errors, status) = bulk_update_fields(
                    request, videos_list, update_fields
                )
                result["fields_errors"] = fields_errors
                counter = len(result["updated_videos"])
                if "transcript" in update_fields:
                    update_action = "transcript"
            elif update_action == "delete":
                # Bulk delete
                deleted_videos, status = bulk_update_delete(request, videos_list)
                counter = len(deleted_videos)
            else:
                pass

            delta = len(selected_videos) - counter
            result, status = get_bulk_update_result(
                request, status, update_action, counter, delta, result
            )
        else:
            status = 400
            result["message"] = _("Sorry, no video found.")
        return JsonResponse(result, status=status)


def bulk_update_fields(request, videos_list, update_fields):
    """
    Perform field(s) bulk update for selected videos.

    Args:
        request (Request): current HTTP Request.
        videos_list (List[Video]): list of videos to be edited.
        update_fields (List[string]): list of field(s) to update.

    Returns:
        updated_videos (List[string]): list of modified videos slugs.
        fields_errors (List[Obj{"field_name":error}]): list of potential fields errors.
        status (number): HTTP status.
    """
    status = 200
    updated_videos = []
    fields_errors = []

    for video in videos_list:
        if "owner" in update_fields:
            new_owner = User.objects.get(pk=request.POST.get("owner")) or None
            if change_owner(video.id, new_owner):
                updated_videos.append(Video.objects.get(pk=video.id).slug)
        else:
            form = VideoForm(
                request.POST,
                request.FILES,
                instance=video,
                is_staff=request.user.is_staff,
                is_superuser=request.user.is_superuser,
                current_user=request.user,
                current_lang=request.LANGUAGE_CODE,
            )
            form.create_with_fields(update_fields)

            if form.is_valid():
                video = save_video_form(request, form)
                updated_videos.append(Video.objects.get(pk=video.id).slug)
            else:
                # Prevent from duplicate error items
                if dict(form.errors.items()) not in fields_errors:
                    fields_errors.append(dict(form.errors.items()))
                status = 400
                break

    return updated_videos, fields_errors, status


def bulk_update_delete(request, videos_list):
    """
    Perform bulk delete for selected videos.

    Args:
        request (Request): current HTTP Request.
        videos_list (List[Video]): list of videos to be deleted.

    Returns:
        deleted_videos (List[string]): list of deleted videos slugs.
        status (number): HTTP status.
    """
    status = 200
    deleted_videos = []

    for video in videos_list:
        if video_is_deletable(request, video):
            slug = video.slug
            video.delete()
            deleted_videos.append(slug)
        else:
            status = 400
            break
    return deleted_videos, status


def get_bulk_update_result(request, status, update_action, counter, delta, result):
    """
    Build and return result object with updated status and message for bulk update action.

    Args:
        request (Request): current HTTP Request.
        status (number): HTTP status.
        update_action (string): Action case ("fields", "delete" or "transcript").
        counter (number): Count of altered videos.
        delta (number): Count of selected videos to be edited.
        result (Obj{message(string), fields_errors(List[Obj]), updated_videos(List[string])}): Current result object.

    Returns:
        result (Obj{message(string), fields_errors(List[Obj]), updated_videos(List[string])}): Updated result object.
        status (number): HTTP status.
    """
    if len(result["fields_errors"]) == 0:
        # Get global error messages (transcript or delete) and set status 400 if error message exists
        if get_max_code_lvl_messages(request) >= 40:
            status = 400
        result["message"] = " ".join(map(str, messages.get_messages(request)))
        result["message"] += " " + get_recap_message_bulk_update(
            request, update_action, counter, delta
        )

    # Prevent alert messages to popup on reload (asynchronous view)
    dismiss_stored_messages(request)

    return result, status


def get_recap_message_bulk_update(request, update_action, counter, delta) -> str:
    """
    Build and return overview message for bulk update.

    Args:
        request (Request): current HTTP Request.
        update_action (string): Action case ("fields", "delete" or "transcript").
        counter (number): Count of altered videos.
        delta (number): Count of selected videos to be edited.

    Returns:
        msg (string): Return pluralized and translated message.
    """
    # Define translations keys and message with plural management
    message_translations = {
        "delete": ngettext(
            "%(counter)s video removed", "%(counter)s videos removed", counter
        )
        % {"counter": counter},
        "transcript": ngettext(
            "%(counter)s video transcripted", "%(counter)s videos transcripted", counter
        )
        % {"counter": counter},
        "fields": ngettext(
            "%(counter)s video modified", "%(counter)s videos modified", counter
        )
        % {"counter": counter},
    }
    # Get plural translation for deleted, transcripted or updated videos
    msg = message_translations[update_action]
    counter = delta
    # Get plural translation for videos in error
    msg += ", " + ngettext(
        "%(counter)s video in error", "%(counter)s videos in error", counter
    ) % {"counter": counter}
    return msg


def get_paginated_videos(paginator, page):
    """Return paginated videos in paginator object."""
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def get_filtered_videos_list(request, videos_list):
    """Return filtered videos list by get parameters."""
    if request.GET.getlist("type"):
        videos_list = videos_list.filter(type__slug__in=request.GET.getlist("type"))
    if request.GET.getlist("discipline"):
        videos_list = videos_list.filter(
            discipline__slug__in=request.GET.getlist("discipline")
        )
    if (
        request.user
        and owner_is_searchable(request.user)
        and request.GET.getlist("owner")
    ):
        # Add filter on additional owners
        videos_list = videos_list.filter(
            Q(owner__username__in=request.GET.getlist("owner"))
            | Q(additional_owners__username__in=request.GET.getlist("owner"))
        )
    if request.GET.getlist("tag"):
        videos_list = videos_list.filter(tags__slug__in=request.GET.getlist("tag"))

    if request.GET.getlist("cursus"):
        videos_list = videos_list.filter(cursus__in=request.GET.getlist("cursus"))
    return videos_list.distinct()


def get_owners_has_instances(owners: list) -> list:
    """Return the list of owners who has instances in User.objects."""
    ownersInstances = []
    for owner in owners:
        try:
            obj = User.objects.get(username=owner)
            ownersInstances.append(obj)
        except ObjectDoesNotExist:
            pass
    return ownersInstances


def owner_is_searchable(user: User) -> bool:
    """
    Check if user is searchable.

    according to HIDE_USER_FILTER setting and authenticated user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        bool: True if HIDE_USER_FILTER is False and user is authenticated, False otherwise
    """
    return not HIDE_USER_FILTER and user.is_authenticated


def videos(request):
    """Render the main list of videos."""
    videos_list = get_filtered_videos_list(request, get_available_videos())
    sort_field = request.GET.get("sort") if request.GET.get("sort") else "date_added"
    sort_direction = request.GET.get("sort_direction")

    videos_list = sort_videos_list(videos_list, sort_field, sort_direction)

    if not sort_field:
        # Get the default Video ordering
        sort_field = Video._meta.ordering[0].lstrip("-")
    count_videos = len(videos_list)

    page = request.GET.get("page", 1)
    if page == "" or page is None:
        page = 1
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(videos_list, 12)
    videos = get_paginated_videos(paginator, page)
    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))
    owner_filter = owner_is_searchable(request.user)

    if is_ajax(request):
        return render(
            request,
            "videos/video_list.html",
            {
                "videos": videos,
                "full_path": full_path,
                "count_videos": count_videos,
                "owner_filter": owner_filter,
            },
        )
    return render(
        request,
        "videos/videos.html",
        {
            "videos": videos,
            "count_videos": count_videos,
            "types": request.GET.getlist("type"),
            "owners": request.GET.getlist("owner"),
            "disciplines": request.GET.getlist("discipline"),
            "tags_slug": request.GET.getlist("tag"),
            "cursus_selected": request.GET.getlist("cursus"),
            "full_path": full_path,
            "ownersInstances": ownersInstances,
            "cursus_list": CURSUS_CODES,
            "sort_field": sort_field,
            "sort_direction": request.GET.get("sort_direction"),
            "owner_filter": owner_filter,
        },
    )


def is_in_video_groups(user, video):
    return user.owner.accessgroup_set.filter(
        code_name__in=[
            name[0] for name in video.restrict_access_to_groups.values_list("code_name")
        ]
    ).exists()


def get_video_access(request, video, slug_private):
    """Return True if access is granted to current user."""
    is_draft = video.is_draft
    is_restricted = video.is_restricted
    is_restricted_to_group = video.restrict_access_to_groups.all().exists()
    """
    is_password_protected = (video.password is not None
                             and video.password != '')
    """
    is_access_protected = (
        is_draft
        or is_restricted
        or is_restricted_to_group
        # or is_password_protected
    )
    if is_access_protected:
        access_granted_for_private = slug_private and slug_private == video.get_hashkey()
        access_granted_for_draft = request.user.is_authenticated and (
            request.user == video.owner
            or request.user.is_superuser
            or request.user.has_perm("video.change_video")
            or (request.user in video.additional_owners.all())
        )
        access_granted_for_restricted = (
            request.user.is_authenticated and not is_restricted_to_group
        )
        access_granted_for_group = (
            (request.user.is_authenticated and is_in_video_groups(request.user, video))
            or request.user == video.owner
            or request.user.is_superuser
            or request.user.has_perm("recorder.add_recording")
            or (request.user in video.additional_owners.all())
        )

        return (
            access_granted_for_private
            or (is_draft and access_granted_for_draft)
            or (is_restricted and access_granted_for_restricted)
            # and is_password_protected is False)
            or (is_restricted_to_group and access_granted_for_group)
            # and is_password_protected is False)
            # or (
            #     is_password_protected
            #     and access_granted_for_draft
            # )
            # or (
            #     is_password_protected
            #     and request.POST.get('password')
            #     and request.POST.get('password') == video.password
            # )
        )

    else:
        return True


@csrf_protect
def video(request, slug, slug_c=None, slug_t=None, slug_private=None):
    """Render a single video."""
    try:
        id = int(slug[: slug.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid video id")

    video = get_object_or_404(Video, id=id, sites=get_current_site(request))

    if (
        video.get_version != "O"
        and request.GET.get("redirect") != "false"
        and video.get_default_version_link(slug_private)
    ):
        query_string = (
            "?%s" % request.META["QUERY_STRING"]
            if (request.META.get("QUERY_STRING"))
            else ""
        )
        return redirect(video.get_default_version_link(slug_private) + query_string)

    template_video = "videos/video.html"
    params = {
        "active_video_comment": ACTIVE_VIDEO_COMMENT,
    }
    if request.GET.get("is_iframe"):
        params = {"page_title": video.title}
        template_video = "videos/video-iframe.html"
    elif request.GET.get("playlist"):
        playlist = get_object_or_404(Playlist, slug=request.GET.get("playlist"))
        if playlist_can_be_displayed(request, playlist) and user_can_see_playlist_video(
            request, video, playlist
        ):
            videos = sort_videos_list(get_video_list_for_playlist(playlist), "rank")
            params = {
                "playlist_in_get": playlist,
                "videos": videos,
            }
        else:
            raise PermissionDenied(
                _("You cannot access this playlist because it is private.")
            )
    return render_video(request, id, slug_c, slug_t, slug_private, template_video, params)


def toggle_render_video_user_can_see_video(
    show_page, is_password_protected, request, slug_private, video
) -> bool:
    """Toogle condition for `render_video()`."""
    return (
        (show_page and not is_password_protected)
        or (
            show_page
            and is_password_protected
            and request.POST.get("password") == video.password
            # and check_password(request.POST.get("password"), video.password)
        )
        or (
            slug_private
            and (
                slug_private == video.get_hashkey()
                or slug_private
                in [
                    str(tok.token) for tok in VideoAccessToken.objects.filter(video=video)
                ]
            )
        )
        or request.user == video.owner
        or request.user.is_superuser
        or request.user.has_perm("video.change_video")
        or (request.user in video.additional_owners.all())
        or (request.GET.get("playlist"))
    )


def toggle_render_video_when_is_playlist_player(request):
    """Toggle `render_video()` when the user want to play a playlist."""
    playlist = get_object_or_404(Playlist, slug=request.GET.get("playlist"))
    if request.user.is_authenticated:
        video = (
            Video.objects.filter(
                playlistcontent__playlist_id=playlist.id,
                is_draft=False,
                is_restricted=False,
            )
            | Video.objects.filter(
                playlistcontent__playlist_id=playlist.id,
                owner=request.user,
            )
        ).first()
    else:
        video = Video.objects.filter(
            playlistcontent__playlist_id=playlist.id,
            is_draft=False,
            is_restricted=False,
        ).first()
    if not video:
        return Http404()


def render_video(
    request,
    id,
    slug_c=None,
    slug_t=None,
    slug_private=None,
    template_video="videos/video.html",
    more_data={},
):
    """Render video."""
    video = get_object_or_404(Video, id=id, sites=get_current_site(request))
    """
    # Do it only for video --> move code in video definition
    app_name = request.resolver_match.namespace.capitalize()[0] \
        if request.resolver_match.namespace else 'O'
    if (
        video.get_version != app_name and
        request.GET.get('redirect') != "false"
    ):
        return redirect(video.get_default_version_link())
    """
    listNotes = get_adv_note_list(request, video)
    channel = (
        get_object_or_404(Channel, slug=slug_c, site=get_current_site(request))
        if slug_c
        else None
    )
    theme = get_object_or_404(Theme, channel=channel, slug=slug_t) if slug_t else None

    is_password_protected = video.password is not None and video.password != ""

    show_page = get_video_access(request, video, slug_private)

    owner_filter = owner_is_searchable(request.user)

    if toggle_render_video_user_can_see_video(
        show_page, is_password_protected, request, slug_private, video
    ):
        playlist = None
        if request.GET.get("playlist"):
            playlist = get_object_or_404(Playlist, slug=request.GET.get("playlist"))
            if not user_can_see_playlist_video(
                request,
                video,
                playlist,
            ):
                toggle_render_video_when_is_playlist_player(request)
        return render(
            request,
            template_video,
            {
                "channel": channel,
                "video": video,
                "theme": theme,
                "listNotes": listNotes,
                "owner_filter": owner_filter,
                "playlist": playlist if request.GET.get("playlist") else None,
                **more_data,
            },
        )
    else:
        is_draft = video.is_draft
        is_restricted = video.is_restricted
        is_restricted_to_group = video.restrict_access_to_groups.all().exists()
        is_access_protected = is_draft or is_restricted or is_restricted_to_group
        if is_password_protected and (
            not is_access_protected or (is_access_protected and show_page)
        ):
            form = (
                VideoPasswordForm(request.POST) if request.POST else VideoPasswordForm()
            )
            if (
                request.POST.get("password")
                and request.POST.get("password") != video.password
                # and check_password(request.POST.get("password"), video.password )
            ):
                messages.add_message(
                    request, messages.ERROR, _("The password is incorrect.")
                )
            return render(
                request,
                "videos/video.html",
                {
                    "channel": channel,
                    "video": video,
                    "theme": theme,
                    "form": form,
                    "listNotes": listNotes,
                    "owner_filter": owner_filter,
                    **more_data,
                },
            )
        elif request.user.is_authenticated:
            messages.add_message(
                request, messages.ERROR, _("You cannot watch this video.")
            )
            raise PermissionDenied
        else:
            iframe_param = "is_iframe=true&" if (request.GET.get("is_iframe")) else ""
            return redirect(
                "%s?%sreferrer=%s"
                % (settings.LOGIN_URL, iframe_param, request.get_full_path())
            )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def video_edit(request, slug=None):
    """Video Edit View."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = (
        get_object_or_404(Video, slug=slug, sites=get_current_site(request))
        if slug
        else None
    )

    if RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "videos/video_edit.html", {"access_not_allowed": True})

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this video."))
        raise PermissionDenied

    # default selected owner in select field
    default_owner = video.owner.pk if video else request.user.pk
    form = VideoForm(
        instance=video,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": default_owner},
    )

    if request.method == "POST":
        form = VideoForm(
            request.POST,
            request.FILES,
            instance=video,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user,
            current_lang=request.LANGUAGE_CODE,
        )
        if form.is_valid():
            video = save_video_form(request, form)
            messages.add_message(
                request, messages.INFO, _("The changes have been saved.")
            )
            if request.POST.get("_saveandsee"):
                return redirect(reverse("video:video", args=(video.slug,)))
            else:
                return redirect(reverse("video:video_edit", args=(video.slug,)))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "videos/video_edit.html",
        {"form": form, "listTheme": json.dumps(get_list_theme_in_form(form))},
    )


def get_list_theme_in_form(form) -> dict:
    """
    Get the themes for the form.

    Args:
        form: the form containing the channel available by the user.

    Returns:
        an array containing all the themes available.
    """
    listTheme = {}
    if "channel" in form.fields:
        for channel in form.fields["channel"].queryset:
            if channel.themes.count() > 0:
                listTheme["channel_%s" % channel.id] = channel.get_all_theme()
    return listTheme


def save_video_form(request, form):
    video = form.save(commit=False)
    if (
        (request.user.is_superuser or request.user.has_perm("video.add_video"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
    ):
        video.owner = form.cleaned_data["owner"]

    elif getattr(video, "owner", None) is None:
        video.owner = request.user
    video.save()
    form.save_m2m()
    video.sites.add(get_current_site(request))
    video.save()
    form.save_m2m()
    return video


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_delete(request, slug=None):
    """View to delete video. Show form to approve deletion and do it if sent."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if video_is_deletable(request, video):
        form = VideoDeleteForm()

        if request.method == "POST":
            form = VideoDeleteForm(request.POST)
            if form.is_valid():
                media_root = settings.MEDIA_ROOT
                temp_file_path = os.path.join(media_root, "temp_video.mp4")
                with open(temp_file_path, "wb") as temp_file:
                    temp_file.write(b"Temporary video content")
                video.video.name = os.path.relpath(temp_file_path, media_root)
                video.save()
                video.delete()

                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

                messages.add_message(
                    request, messages.INFO, _("The media has been deleted.")
                )
                return redirect(reverse("video:dashboard"))
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("One or more errors have been found in the form."),
                )
        page_title = _('Deleting the media "%(vtitle)s"') % {"vtitle": video.title}
        return render(
            request,
            "videos/video_delete.html",
            {"video": video, "form": form, "page_title": page_title},
        )
    else:
        # If the video is not deletable, the video_is_deletable function will raise
        # a PermissionDenied exception or an error message will be displayed.
        return redirect(reverse("video:dashboard"))


def video_is_deletable(request, video) -> bool:
    """Check if video is deletable, usage for delete form and multiple deletion."""
    if request.user != video.owner and not (
        request.user.is_superuser or request.user.has_perm("video.delete_video")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot delete this media."))
        raise PermissionDenied

    if WEBTV_MODE:
        if video.encoding_in_progress is True:
            messages.add_message(
                request,
                messages.ERROR,
                _("You cannot delete a media that is being encoded."),
            )
            return False
        return True
    else:
        if not video.encoded or video.encoding_in_progress is True:
            messages.add_message(
                request,
                messages.ERROR,
                _("You cannot delete a media that is being encoded."),
            )
            return False
        return True


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_edit_access_tokens(request: WSGIRequest, slug: str = None):
    """View to manage access token of a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this video."))
        raise PermissionDenied
    if request.method == "POST":
        if request.POST.get("action") and request.POST.get("action") in {
            "add",
            "delete",
            "update",
        }:
            if request.POST["action"] == "add":
                VideoAccessToken.objects.create(video=video)
                messages.add_message(
                    request, messages.SUCCESS, _("A token has been created.")
                )
            elif request.POST["action"] == "delete" and request.POST.get("token"):
                token = request.POST.get("token")
                delete_token(request, video, token)
            elif request.POST["action"] == "update":
                token = request.POST.get("token")
                update_token(request, video, token)
            else:
                messages.add_message(request, messages.ERROR, _("Token not found."))
        else:
            messages.add_message(
                request, messages.ERROR, _("An action must be specified.")
            )
        # redirect to remove post data
        return redirect(reverse("video:video_edit_access_tokens", args=(video.slug,)))
    tokens = VideoAccessToken.objects.filter(video=video)
    page_title = _('Manage access tokens for the video "%(vtitle)s"') % {
        "vtitle": video.title
    }
    return render(
        request,
        "videos/video_access_tokens.html",
        {"video": video, "tokens": tokens, "page_title": page_title},
    )


def delete_token(request, video: Video, token: VideoAccessToken):
    """Remove token for the video if exist."""
    try:
        uuid.UUID(str(token))
        VideoAccessToken.objects.get(video=video, token=token).delete()
        messages.add_message(request, messages.SUCCESS, _("The token has been deleted."))
    except (ValueError, ObjectDoesNotExist):
        messages.add_message(request, messages.ERROR, _("Token not found."))


def update_token(request, video: Video, token: VideoAccessToken):
    """update token name for the video if exist."""
    try:
        Token = VideoAccessToken.objects.get(video=video, token=token)
        Token.name = request.POST.get("name")
        Token.save()
        messages.add_message(request, messages.SUCCESS, _("The token has been updated."))
    except (ValueError, ObjectDoesNotExist):
        messages.add_message(request, messages.ERROR, _("Token not found."))


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_transcript(request, slug=None):
    """View to restart transcription of a video."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))

    if not USE_TRANSCRIPTION:
        messages.add_message(
            request, messages.ERROR, _("Transcription not enabled on this platform.")
        )
        raise PermissionDenied

    if request.user != video.owner and not (
        request.user.is_superuser or request.user.has_perm("video.change_video")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot manage this video."))
        raise PermissionDenied

    if not video.encoded or video.encoding_in_progress is True:
        messages.add_message(
            request,
            messages.ERROR,
            _("You cannot launch transcript for a video that is being encoded."),
        )
        return redirect(reverse("video:video_edit", args=(video.slug,)))

    if video.get_video_mp3():
        available_transcript_lang = [lang[0] for lang in get_transcription_choices()]
        if (
            request.GET.get("lang", "") != ""
            and request.GET["lang"] in available_transcript_lang
        ):
            if video.transcript != request.GET["lang"]:
                video.transcript = request.GET["lang"]
                video.save()
            transcript_video = getattr(transcript, TRANSCRIPT_VIDEO)
            transcript_video(video.id)
            messages.add_message(
                request, messages.INFO, _("The video transcript has been restarted.")
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("An available transcription language must be specified."),
            )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("No audio file found."),
        )
    return redirect(reverse("video:video_edit", args=(video.slug,)))


def get_adv_note_list(request, video):
    """Return the list of AdvancedNotes of video that can be seen by the current user."""
    if request.user.is_authenticated:
        filter = (
            Q(user=request.user)
            | (Q(video__owner=request.user) & Q(status="1"))
            | Q(status="2")
        )
    else:
        filter = Q(status="2")
    return (
        AdvancedNotes.objects.all()
        .filter(video=video)
        .filter(filter)
        .order_by("timestamp", "added_on")
    )


def get_adv_note_com_list(request, id):
    """
    Return the list of coms which are direct sons of the AdvancedNote id.

        ...that can be seen by the current user
    """
    if id:
        note = get_object_or_404(AdvancedNotes, id=id)
        if request.user.is_authenticated:
            filter = (
                Q(user=request.user)
                | (Q(parentNote__video__owner=request.user) & Q(status="1"))
                | Q(status="2")
            )
        else:
            filter = Q(status="2")
        return (
            NoteComments.objects.all()
            .filter(parentNote=note, parentCom=None)
            .filter(filter)
            .order_by("added_on")
        )
    else:
        return []


def get_com_coms_dict(request, listComs):
    """
    Return the list of the direct sons of a com.

      for each encountered com
    Starting from the coms present in listComs
    Example, having the next tree of coms:
    |- C1     (id: 1)
    |- C2     (id: 2)
       |- C3  (id: 3)
    With listComs = [C1, C2]
    The result will be {'1': [], '2': [C3], '3': []}
    """
    dictComs = dict()
    if not listComs:
        return dictComs
    if request.user.is_authenticated:
        filter = (
            Q(user=request.user)
            | (Q(parentNote__video__owner=request.user) & Q(status="1"))
            | Q(status="2")
        )
    else:
        filter = Q(status="2")
    for c in listComs:
        lComs = (
            NoteComments.objects.all()
            .filter(parentCom=c)
            .filter(filter)
            .order_by("added_on")
        )
        dictComs[str(c.id)] = lComs
        dictComs.update(get_com_coms_dict(request, lComs))
    return dictComs


def get_com_tree(com):
    """
    Return the list of the successive parents of com.

      including com from bottom to top
    """
    tree, c = [], com
    while c.parentCom is not None:
        tree.append(c)
        c = c.parentCom
    tree.append(c)
    return tree


def can_edit_or_remove_note_or_com(request, nc, action) -> None:
    """
    Check if the current user can apply action to the note or comment nc.

    Typically action is in ['edit', 'delete']
    If not raise PermissionDenied
    """
    if request.user != nc.user and not (
        request.user.is_superuser
        or (
            request.user.has_perm("video.change_notes")
            and request.user.has_perm("video.delete_notes")
            and request.user.has_perm("video.change_advancednotes")
            and request.user.has_perm("video.delete_advancednotes")
        )
    ):
        messages.add_message(
            request,
            messages.WARNING,
            _("You cannot %s this note or comment." % action),
        )
        raise PermissionDenied


def can_see_note_or_com(request, nc) -> None:
    """
    Check if the current user can view the note or comment nc.

    If not raise PermissionDenied
    """
    if isinstance(nc, AdvancedNotes):
        vid_owner = nc.video.owner
    elif isinstance(nc, NoteComments):
        vid_owner = nc.parentNote.video.owner
    if not (
        request.user == nc.user
        or (request.user == vid_owner and nc.status == "1")
        or nc.status == "2"
        or (
            request.user.is_superuser
            or (
                request.user.has_perm("video.change_notes")
                and request.user.has_perm("video.change_advancednotes")
            )
        )
    ):
        messages.add_message(
            request,
            messages.WARNING,
            _("You cannot see this note or comment."),
        )
        raise PermissionDenied


@csrf_protect
def video_notes(request, slug):
    """Render video notes."""
    action = None
    if request.method == "POST" and request.POST.get("action"):
        action = request.POST.get("action").split("_")[0]
    elif request.method == "GET" and request.GET.get("action"):
        action = request.GET.get("action").split("_")[0]
    if action in __NOTE_ACTION__:
        return eval("video_note_{0}(request, slug)".format(action))
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    listNotes = get_adv_note_list(request, video)
    return render(
        request,
        "videos/video_notes.html",
        {"video": video, "listNotes": listNotes},
    )


@csrf_protect
def video_note_get(request, slug):
    """Get video notes."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idCom = get_id_from_request(request, "idCom")
    idNote = get_id_from_request(request, "idNote")

    if idNote is None:
        listNotes = get_adv_note_list(request, video)
        return render(
            request,
            "videos/video_notes.html",
            {"video": video, "listNotes": listNotes},
        )
    else:
        note = get_object_or_404(AdvancedNotes, id=idNote)
        can_see_note_or_com(request, note)
        if idCom is not None:
            com = get_object_or_404(NoteComments, id=idCom)
            can_see_note_or_com(request, com)
            comToDisplay = get_com_tree(com)
        else:
            comToDisplay = None

        listNotes = get_adv_note_list(request, video)
        listComments = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listComments)
        return render(
            request,
            "videos/video_notes.html",
            {
                "video": video,
                "noteToDisplay": note,
                "comToDisplay": comToDisplay,
                "listNotes": listNotes,
                "listComments": listComments,
                "dictComments": dictComments,
            },
        )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_note_form(request, slug):
    """Render video note form."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idNote, idCom = None, None
    note, com = None, None
    idCom = get_id_from_request(request, "idCom")
    idNote = get_id_from_request(request, "idNote")

    if idCom is not None:
        com = get_object_or_404(NoteComments, id=idCom)
    if idNote is not None:
        note = get_object_or_404(AdvancedNotes, id=idNote)

    params = (idNote, idCom, note, com)
    res = video_note_form_case(request, params)
    (
        note,
        com,
        noteToDisplay,
        comToDisplay,
        noteToEdit,
        comToEdit,
        listNotesCom,
        dictComments,
        form,
    ) = res
    listNotes = get_adv_note_list(request, video)

    return render(
        request,
        "videos/video_notes.html",
        {
            "video": video,
            "noteToDisplay": noteToDisplay,
            "comToDisplay": comToDisplay,
            "noteToEdit": noteToEdit,
            "comToEdit": comToEdit,
            "listNotes": listNotes,
            "listComments": listNotesCom,
            "dictComments": dictComments,
            "note_form": form,
        },
    )


def video_note_form_case(request, params):
    """Editing/creating a note."""
    (idNote, idCom, note, com) = params
    noteToDisplay, comToDisplay = None, None
    listNotesCom, dictComments = None, None
    comToEdit, noteToEdit = None, None
    # Editing a note comment
    if (
        idCom is not None
        and idNote is not None
        and (
            (request.method == "POST" and request.POST.get("action") == "form_com_edit")
            or (request.method == "GET" and request.GET.get("action") == "form_com_edit")
        )
    ):
        can_edit_or_remove_note_or_com(request, com, "edit")
        form = NoteCommentsForm({"comment": com.comment, "status": com.status})
        noteToDisplay, comToDisplay = note, get_com_tree(com)
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
        comToEdit = com
        # Creating a comment answer
    elif (
        idCom is not None
        and idNote is not None
        and (
            (request.method == "POST" and request.POST.get("action") == "form_com_new")
            or (request.method == "GET" and request.GET.get("action") == "form_com_new")
        )
    ):
        form = NoteCommentsForm()
        noteToDisplay, comToDisplay = note, get_com_tree(com)
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
    # Editing a note
    elif (
        idCom is None
        and idNote is not None
        and (
            (request.method == "POST" and request.POST.get("action") == "form_note")
            or (request.method == "GET" and request.GET.get("action") == "form_note")
        )
    ):
        can_edit_or_remove_note_or_com(request, note, "delete")
        form = AdvancedNotesForm(
            {
                "timestamp": note.timestamp,
                "note": note.note,
                "status": note.status,
            }
        )
        noteToEdit = note
    # Creating a note comment
    elif (
        idCom is None
        and idNote is not None
        and (
            (request.method == "POST" and request.POST.get("action") == "form_com")
            or (request.method == "GET" and request.GET.get("action") == "form_com")
        )
    ):
        form = NoteCommentsForm()
        noteToDisplay, comToDisplay = note, None
        listNotesCom = get_adv_note_com_list(request, idNote)
    # Creating a note
    elif idCom is None and idNote is None:
        form = AdvancedNotesForm()
    return (
        note,
        com,
        noteToDisplay,
        comToDisplay,
        noteToEdit,
        comToEdit,
        listNotesCom,
        dictComments,
        form,
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_note_save(request, slug):
    """Save a Video note or comment."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idNote, idCom = None, None
    note, com = None, None
    noteToDisplay, comToDisplay = None, None
    noteToEdit, comToEdit = None, None
    listNotesCom, dictComments = None, None
    form = None

    idCom = get_id_from_request(request, "idCom")
    idNote = get_id_from_request(request, "idNote")

    if idCom:
        com = NoteComments.objects.get(id=idCom)
    if idNote:
        note = AdvancedNotes.objects.get(id=idNote)

    if request.method == "POST" and request.POST.get("action") == "save_note":
        q = QueryDict(mutable=True)
        q.update(request.POST)
        q.update({"video": video.id})
        form = AdvancedNotesForm(q)
        noteToEdit = note
    elif request.method == "POST" and (request.POST.get("action").startswith("save_com")):
        form = NoteCommentsForm(request.POST)
        comToEdit = {
            "save_com": com,
            "save_com_edit": com,
            "save_com_new": None,
        }[request.POST.get("action")]

    params = (
        idNote,
        idCom,
        note,
        com,
        noteToDisplay,
        comToDisplay,
        listNotesCom,
        dictComments,
    )
    if request.method == "POST" and form and form.is_valid():
        form = None
        res = video_note_save_form_valid(request, video, params)
        (
            note,
            com,
            noteToDisplay,
            comToDisplay,
            listNotesCom,
            dictComments,
        ) = res
    elif request.method == "POST" and form and not form.is_valid():
        res = video_note_form_not_valid(request, params)
        (
            note,
            com,
            noteToDisplay,
            comToDisplay,
            listNotesCom,
            dictComments,
        ) = res

    listNotes = get_adv_note_list(request, video)
    return render(
        request,
        "videos/video_notes.html",
        {
            "video": video,
            "noteToDisplay": noteToDisplay,
            "comToDisplay": comToDisplay,
            "noteToEdit": noteToEdit,
            "comToEdit": comToEdit,
            "listNotes": listNotes,
            "listComments": listNotesCom,
            "dictComments": dictComments,
            "note_form": form,
        },
    )


def video_note_save_form_valid(request, video, params):
    """Save a note or a note comment."""
    (
        idNote,
        idCom,
        note,
        com,
        noteToDisplay,
        comToDisplay,
        listNotesCom,
        dictComments,
    ) = params
    # Saving a com after an edit
    if (
        idCom is not None
        and idNote is not None
        and request.POST.get("action") == "save_com_edit"
    ):
        com.comment = request.POST.get("comment")
        com.status = request.POST.get("status")
        com.modified_on = timezone.now()
        com.save()
        messages.add_message(request, messages.INFO, _("The comment has been modified."))
        noteToDisplay, comToDisplay = note, get_com_tree(com)
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
    # Saving a new answer (com) to a note
    elif (
        idCom is not None
        and idNote is not None
        and request.POST.get("action") == "save_com_new"
    ):
        com2 = NoteComments.objects.create(
            user=request.user,
            parentNote=note,
            parentCom=com,
            status=request.POST.get("status"),
            comment=request.POST.get("comment"),
        )
        messages.add_message(request, messages.INFO, _("The comment has been saved."))
        noteToDisplay = note
        comToDisplay = get_com_tree(com2)
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
    # Saving a note after an edit
    elif (
        idCom is None and idNote is not None and request.POST.get("action") == "save_note"
    ):
        note.note = request.POST.get("note")
        note.status = request.POST.get("status")
        note.modified_on = timezone.now()
        note.save()
        messages.add_message(request, messages.INFO, _("Your note has been modified."))
    # Saving a new com for a note
    elif (
        idCom is None and idNote is not None and request.POST.get("action") == "save_com"
    ):
        com = NoteComments.objects.create(
            user=request.user,
            parentNote=note,
            status=request.POST.get("status"),
            comment=request.POST.get("comment"),
        )
        messages.add_message(request, messages.INFO, _("Your comment has been saved."))
        noteToDisplay = note
        listNotesCom = get_adv_note_com_list(request, idNote)
    # Saving a new note
    elif idCom is None and idNote is None:
        timestamp = request.POST.get("timestamp")
        note, created = AdvancedNotes.objects.get_or_create(
            user=request.user,
            video=video,
            status=request.POST.get("status"),
            timestamp=timestamp,
        )
        if created or not note.note:
            note.note = request.POST.get("note")
            message = _("The note has been saved.")
        else:
            # If there is already a note at this timestamp & status, update it.
            note.note = note.note + "\n" + request.POST.get("note")
            message = _(
                "Your note at %(timestamp)s has been modified."
                % {"timestamp": note.timestampstr()}
            )
        note.save()
        messages.add_message(request, messages.INFO, message)

    return (note, com, noteToDisplay, comToDisplay, listNotesCom, dictComments)


def video_note_form_not_valid(request, params):
    """Display a warning when a note or a note comment is not valid."""
    (
        idNote,
        idCom,
        note,
        com,
        noteToDisplay,
        comToDisplay,
        listNotesCom,
        dictComments,
    ) = params
    messages.add_message(
        request,
        messages.WARNING,
        _("One or more errors have been found in the form."),
    )
    if (
        (idCom is not None and idNote is not None)
        or (idCom is not None and idNote is None)
        or (
            idCom is None
            and idNote is not None
            and request.POST.get("action") == "save_com"
        )
    ):
        noteToDisplay = note
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
    return (note, com, noteToDisplay, comToDisplay, listNotesCom, dictComments)


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_note_remove(request, slug):
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    if request.method == "POST":
        idCom = idNote = noteToDisplay = listNotesCom = None
        if request.POST.get("idCom"):
            idCom = request.POST.get("idCom")
            com = get_object_or_404(NoteComments, id=idCom)
        if request.POST.get("idNote"):
            idNote = request.POST.get("idNote")
            note = get_object_or_404(AdvancedNotes, id=idNote)

        if idNote and request.POST.get("action") == "remove_note":
            can_edit_or_remove_note_or_com(request, note, "delete")
            note.delete()
            messages.add_message(request, messages.INFO, _("The note has been deleted."))
            listNotesCom, comToDisplay = None, None
        elif idNote and idCom and request.POST.get("action") == "remove_com":
            can_edit_or_remove_note_or_com(request, com, "delete")
            comToDisplay = get_com_tree(com)
            com.delete()
            messages.add_message(
                request, messages.INFO, _("The comment has been deleted.")
            )
            noteToDisplay = note
            listNotesCom = get_adv_note_com_list(request, idNote)

    listNotes = get_adv_note_list(request, video)
    dictComments = get_com_coms_dict(request, listNotesCom)
    return render(
        request,
        "videos/video_notes.html",
        {
            "video": video,
            "noteToDisplay": noteToDisplay,
            "comToDisplay": comToDisplay,
            "listNotes": listNotes,
            "listComments": listNotesCom,
            "dictComments": dictComments,
        },
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_note_download(request, slug):
    """Download all notes of a video in CSV format."""
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    listNotes = get_adv_note_list(request, video)
    contentToDownload = {
        "type": [],
        "id": [],
        "status": [],
        "relatedNote": [],
        "relatedComment": [],
        "dateCreated": [],
        "dataModified": [],
        "noteTimestamp": [],
        "content": [],
    }

    def write_to_dict(t, id, s, rn, rc, dc, dm, nt, c) -> None:
        contentToDownload["type"].append(t)
        contentToDownload["id"].append(id)
        contentToDownload["status"].append(s)
        contentToDownload["relatedNote"].append(rn)
        contentToDownload["relatedComment"].append(rc)
        contentToDownload["dateCreated"].append(dc)
        contentToDownload["dataModified"].append(dm)
        contentToDownload["noteTimestamp"].append(nt)
        contentToDownload["content"].append(c)

    def rec_expl_coms(idNote, lComs) -> None:
        dictComs = get_com_coms_dict(request, lComs)
        for c in lComs:
            write_to_dict(
                str(_("Comment")),
                str(c.id),
                dict(NOTES_STATUS)[c.status],
                str(idNote),
                (str(c.parentCom.id) if c.parentCom else str(_("None"))),
                c.added_on.strftime("%Y-%d-%m"),
                c.modified_on.strftime("%Y-%d-%m"),
                str(_("None")),
                c.comment,
            )
            rec_expl_coms(idNote, dictComs[str(c.id)])

    for n in listNotes:
        write_to_dict(
            str(_("Note")),
            str(n.id),
            dict(NOTES_STATUS)[n.status],
            str(_("None")),
            str(_("None")),
            n.added_on.strftime("%Y-%d-%m"),
            n.modified_on.strftime("%Y-%d-%m"),
            n.timestampstr(),
            n.note,
        )
        lComs = get_adv_note_com_list(request, n.id)
        rec_expl_coms(n.id, lComs)

    df = pandas.DataFrame(
        contentToDownload,
        columns=[
            "type",
            "id",
            "status",
            "relatedNote",
            "relatedComment",
            "dateCreated",
            "dataModified",
            "noteTimestamp",
            "content",
        ],
    )
    df.columns = [
        str(_("Type")),
        str(_("ID")),
        str(_("Status")),
        str(_("Parent note id")),
        str(_("Parent comment id")),
        str(_("Created on")),
        str(_("Modified on")),
        str(_("Note timestamp")),
        str(_("Content")),
    ]
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        "attachment; \
        filename=%s_notes_and_comments.csv"
        % slug
    )
    df.to_csv(
        path_or_buf=response,
        sep="|",
        float_format="%.2f",
        index=False,
        decimal=",",
    )
    return response


@csrf_protect
def video_count(request, id):
    """View to store the video count."""
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        try:
            view_count = ViewCount.objects.get(video=video, date=date.today())
        except ViewCount.DoesNotExist:
            try:
                with transaction.atomic():
                    ViewCount.objects.create(video=video, count=1)
                    return HttpResponse("ok")
            except IntegrityError:
                view_count = ViewCount.objects.get(video=video, date=date.today())
        view_count.count = F("count") + 1
        view_count.save(update_fields=["count"])
        return HttpResponse("ok")
    messages.add_message(request, messages.ERROR, _("You cannot access to this view."))
    raise PermissionDenied


@login_required(redirect_field_name="referrer")
def video_marker(request, id, time):
    """View to store the video marker time for the authenticated user."""
    video = get_object_or_404(Video, id=id)
    try:
        marker_time = UserMarkerTime.objects.get(video=video, user=request.user)
    except UserMarkerTime.DoesNotExist:
        try:
            with transaction.atomic():
                marker_time = UserMarkerTime.objects.create(
                    video=video, user=request.user, markerTime=time
                )
                return HttpResponse("ok")
        except IntegrityError:
            marker_time = UserMarkerTime.objects.get(video=video, user=request.user)
    marker_time.markerTime = time
    marker_time.save(update_fields=["markerTime"])
    return HttpResponse("ok")


@csrf_protect
@login_required(redirect_field_name="referrer")
def video_version(request, id):
    video = get_object_or_404(Video, id=id, sites=get_current_site(request))
    if request.POST:
        q = QueryDict(mutable=True)
        q.update(request.POST)
        q.update({"video": video.id})
        form = VideoVersionForm(q)
        if form.is_valid():
            videoversion, created = VideoVersion.objects.update_or_create(
                video=video, defaults={"version": request.POST.get("version")}
            )
            return HttpResponse("ok")
        else:
            some_data_to_dump = {
                "errors": "%s" % _("Please correct errors"),
                "form": form.errors,
            }
            data = json.dumps(some_data_to_dump)
            return HttpResponse(data, content_type="application/json")
    messages.add_message(request, messages.ERROR, _("You cannot access to this view."))
    raise PermissionDenied


def video_oembed(request):
    if not request.GET.get("url"):
        raise SuspiciousOperation("URL must be specified")
    format = "xml" if request.GET.get("format") == "xml" else "json"
    version = request.GET.get("version") if request.GET.get("version") else "video"
    data = {}
    data["type"] = "video"
    data["version"] = "1.0"
    data["provider_name"] = __TITLE_SITE__
    protocole = "https" if request.is_secure() else "http"
    data["provider_url"] = "%s://%s" % (
        protocole,
        get_current_site(request).domain,
    )
    data["width"] = 640
    data["height"] = 360

    reg = (
        r"^https?://(.*)/video/(?P<slug>[\-\d\w]+)/"
        + r"(?P<slug_private>[\-\d\w]+)?/?(.*)"
    )
    url = request.GET.get("url")
    p = re.compile(reg)
    m = p.match(url)

    if m and m.group("slug") not in ["add", "edit"]:
        video_slug = m.group("slug")
        slug_private = m.group("slug_private")
        try:
            id = int(video_slug[: video_slug.find("-")])
        except ValueError:
            raise SuspiciousOperation("Invalid video id")
        video = get_object_or_404(Video, id=id, sites=get_current_site(request))

        data["title"] = video.title
        data["author_name"] = video.owner.get_full_name()
        data["author_url"] = "%s%s?owner=%s" % (
            data["provider_url"],
            reverse("videos:videos"),
            video.owner.username,
        )
        video_url = (
            reverse("video:video", kwargs={"slug": video.slug})
            if version == "video"
            else reverse(
                "%(version)s:video_%(version)s" % {"version": version},
                kwargs={"slug": video.slug},
            )
        )
        data["html"] = (
            '<iframe src="%(provider)s%(video_url)s%(slug_private)s'
            + '?is_iframe=true" width="640" height="360" '
            + 'style="padding: 0; margin: 0; border:0" '
            + "allowfullscreen loading='lazy'></iframe>"
        ) % {
            "provider": data["provider_url"],
            "video_url": video_url,
            "slug_private": "%s/" % slug_private if slug_private else "",
        }
        data["thumbnail_url"] = "%s:%s" % (protocole, video.get_thumbnail_url())
        if hasattr(video.thumbnail, "file"):
            data["thumbnail_width"] = video.thumbnail.file.width
            data["thumbnail_height"] = video.thumbnail.file.height
        else:
            data["thumbnail_width"] = 280
            data["thumbnail_height"] = 140
    else:
        return HttpResponseNotFound("<h1>Url not match</h1>")
    if format == "xml":
        xml = """
            <oembed>
                <html>
                    %(html)s
                </html>
                <title>%(title)s</title>
                <provider_name>%(provider_name)s</provider_name>
                <author_url>%(author_url)s</author_url>
                <height>%(height)s</height>
                <provider_url>%(provider_url)s</provider_url>
                <type>video</type>
                <width>%(width)s</width>
                <version>1.0</version>
                <author_name>%(author_name)s</author_name>
                <thumbnail_url>%(thumbnail_url)s</thumbnail_url>
                <thumbnail_width>%(thumbnail_width)s</thumbnail_width>
                <thumbnail_height>%(thumbnail_height)s</thumbnail_height>
            </oembed>
        """ % {
            "html": data["html"].replace("<", "&lt;").replace(">", "&gt;"),
            "title": data["title"],
            "provider_name": data["provider_name"],
            "author_url": data["author_url"],
            "height": data["height"],
            "provider_url": data["provider_url"],
            "width": data["width"],
            "author_name": data["author_name"],
            "thumbnail_url": data["thumbnail_url"],
            "thumbnail_width": data["thumbnail_width"],
            "thumbnail_height": data["thumbnail_height"],
        }
        return HttpResponse(xml, content_type="application/xhtml+xml")
        # return HttpResponseNotFound('<h1>XML not implemented</h1>')
    else:
        return JsonResponse(data)


def get_all_views_count(v_id, date_filter=date.today()):
    all_views = {}

    # view count in day
    count = ViewCount.objects.filter(video_id=v_id, date=date_filter).aggregate(
        Sum("count")
    )["count__sum"]
    all_views["day"] = count if count else 0

    # view count in month
    count = ViewCount.objects.filter(
        video_id=v_id,
        date__year=date_filter.year,
        date__month=date_filter.month,
    ).aggregate(Sum("count"))["count__sum"]
    all_views["month"] = count if count else 0

    # view count in year
    count = ViewCount.objects.filter(
        date__year=date_filter.year, video_id=v_id
    ).aggregate(Sum("count"))["count__sum"]
    all_views["year"] = count if count else 0

    # view count since video was created
    count = ViewCount.objects.filter(video_id=v_id).aggregate(Sum("count"))["count__sum"]
    all_views["since_created"] = count if count else 0

    # playlist addition in day
    count = PlaylistContent.objects.filter(
        video_id=v_id, date_added__date=date_filter
    ).count()
    all_views["playlist_day"] = count if count else 0

    # playlist addition in month
    count = PlaylistContent.objects.filter(
        video_id=v_id,
        date_added__year=date_filter.year,
        date_added__month=date_filter.month,
    ).count()
    all_views["playlist_month"] = count if count else 0

    # playlist addition in year
    count = PlaylistContent.objects.filter(
        video_id=v_id,
        date_added__year=date_filter.year,
    ).count()
    all_views["playlist_year"] = count if count else 0

    # playlist addition since video was created
    count = PlaylistContent.objects.filter(video_id=v_id).count()
    all_views["playlist_since_created"] = count if count else 0

    favorites_playlists = Playlist.objects.filter(name=FAVORITE_PLAYLIST_NAME)

    # favorite addition in day
    count = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists, video_id=v_id, date_added__date=date_filter
    ).count()
    all_views["fav_day"] = count if count else 0

    # favorite addition in month
    count = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists,
        video_id=v_id,
        date_added__year=date_filter.year,
        date_added__month=date_filter.month,
    ).count()
    all_views["fav_month"] = count if count else 0

    # favorite addition in year
    count = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists, video_id=v_id, date_added__year=date_filter.year
    ).count()
    all_views["fav_year"] = count if count else 0

    # favorite addition since video was created
    count = PlaylistContent.objects.filter(
        playlist__in=favorites_playlists,
        video_id=v_id,
    ).count()
    all_views["fav_since_created"] = count if count else 0

    return all_views


def get_videos(p_slug, target, p_slug_t=None):
    """Retourne une ou plusieurs videos selon le slug donné.

    Renvoi vidéo/s et titre de
    (theme, ou video ou channel ou videos pour toutes)
    selon la réference du slug donnée
    (video ou channel ou theme ou videos pour toutes les videos)
    """
    videos = []
    title = _("Pod video viewing statistics")
    available_videos = get_available_videos()
    if target.lower() == "video":
        video_founded = Video.objects.filter(slug=p_slug).first()
        # In case that the slug is a bad one
        if video_founded:
            videos.append(video_founded)
            title = (
                _("Video viewing statistics for %s") % video_founded.title.capitalize()
            )

    elif target.lower() == "channel":
        title = _("Video viewing statistics for the channel %s") % p_slug
        videos = available_videos.filter(channel__slug__istartswith=p_slug)

    elif target.lower() == "theme" and p_slug_t:
        title = _("Video viewing statistics for the theme %s") % p_slug_t
        videos = available_videos.filter(theme__slug__istartswith=p_slug_t)

    elif target == "videos":
        return (available_videos, title)

    return (videos, title)


def get_videos_for_owner(request: WSGIRequest):
    """
    Retrieve a list of videos associated with the current user.

    Args:
        request (HttpRequest): The HTTP request object containing the user.

    Returns:
        list: A video list of specific user.
    """
    site = get_current_site(request)
    # Videos list which user is the owner + which user is an additional owner
    videos_list = request.user.video_set.filter(
        sites=site
    ) | request.user.owners_videos.filter(sites=site)
    return videos_list.distinct()


def view_stats_if_authenticated(user) -> bool:
    if VIEW_STATS_AUTH and user.__str__() == "AnonymousUser":
        return False
    return True


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
            {"form": form, "page_title": page_title},
        )
    elif (
        (not has_rights and video_access_ok and not is_password_protected)
        or (video_access_ok and not is_password_protected)
        or has_rights
    ):
        highlight = request.GET.get("highlight", None)
        if highlight not in (
            "playlist_since_created",
            "since_created",
            "fav_since_created",
        ):
            highlight = None
        return render(
            request,
            "videos/video_stats_view.html",
            {"page_title": page_title, "highlight": highlight},
        )
    return HttpResponseNotFound(
        _("You do not have access rights to this video: %s " % video.slug)
    )


@user_passes_test(view_stats_if_authenticated, redirect_field_name="referrer")
def stats_view(request, slug=None, slug_t=None):
    """
    View for statistics.

    " slug reference video's slug or channel's slug
    " t_slug reference theme's slug
    " from defined the source of the request such as
    " (videos, video, channel or theme)
    """
    target = request.GET.get("from", "videos")
    videos, title = get_videos(slug, target, slug_t)
    error_message = (
        "The following %(target)s does not exist or contain any videos: %(slug)s"
    )
    if request.method == "GET" and target == "video" and videos:
        return manage_access_rights_stats_video(request, videos[0], title)

    elif request.method == "GET" and target == "video" and not videos:
        return HttpResponseNotFound(_("The following video does not exist: %s") % slug)

    if request.method == "GET" and (
        not videos and target in ("channel", "theme", "videos")
    ):
        slug = slug if not slug_t else slug_t
        target = "Pod" if target == "videos" else target
        return HttpResponseNotFound(_(error_message) % {"target": target, "slug": slug})

    if (
        request.method == "POST"
        and target == "video"
        and (
            request.POST.get("password")
            and request.POST.get("password") == videos[0].password
            # and check_password(request.POST.get("password"), videos[0].password)
        )
    ) or (
        request.method == "GET" and videos and target in ("videos", "channel", "theme")
    ):
        return render(request, "videos/video_stats_view.html", {"page_title": title})
    else:
        date_filter = request.POST.get("periode", date.today())
        if isinstance(date_filter, str):
            date_filter = parse(date_filter).date()

        data = list(
            map(
                lambda v: {
                    "title": v.title,
                    "slug": v.slug,
                    **get_all_views_count(v.id, date_filter),
                },
                videos,
            )
        )

        min_date = (
            get_available_videos().aggregate(Min("date_added"))["date_added__min"].date()
        )
        data.append({"min_date": min_date})

        return JsonResponse(data, safe=False)


@login_required(redirect_field_name="referrer")
def video_add(request):
    """Video add view."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    allow_extension = ".%s" % ", .".join(map(str, VIDEO_ALLOWED_EXTENSIONS))
    slug = request.GET.get("slug", "")
    if slug != "":
        try:
            video = Video.objects.get(slug=slug, sites=get_current_site(request))
            if (
                RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY
                and request.user.is_staff is False
            ):
                return HttpResponseNotFound("<h1>Permission Denied</h1>")

            if (
                video
                and request.user != video.owner
                and (
                    not (
                        request.user.is_superuser
                        or request.user.has_perm("video.change_video")
                    )
                )
                and (request.user not in video.additional_owners.all())
            ):
                return HttpResponseNotFound("<h1>Permission Denied</h1>")
        except Video.DoesNotExist:
            pass
    allowed_text = _("The following formats are supported: %s") % ", ".join(
        map(str, VIDEO_ALLOWED_EXTENSIONS)
    )
    return render(
        request,
        "videos/add_video.html",
        {
            "slug": slug,
            "max_size": VIDEO_MAX_UPLOAD_SIZE,
            "allow_extension": allow_extension,
            "allowed_text": allowed_text,
            "restricted_to_staff": RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY,
            "TRANSCRIPT": get_transcription_choices(),
            "page_title": _("Media upload"),
        },
    )


def vote_get(request, video_slug):
    if request.method == "POST":
        return HttpResponseNotFound("<h1>Method Not Allowed</h1>", status=405)
    else:
        c_video = get_object_or_404(Video, slug=video_slug)
        if request.user.id is None:  # Anonymous user
            return HttpResponse(
                json.dumps({"comments_votes": []}),
                content_type="application/json",
            )
        votes = Vote.objects.filter(comment__video=c_video, user=request.user).values(
            "comment__id"
        )
        return HttpResponse(
            json.dumps({"comments_votes": list(votes)}),
            content_type="application/json",
        )


@ajax_login_required
@csrf_protect
def vote_post(request, video_slug, comment_id):
    if request.method == "GET":
        return HttpResponseNotFound("<h1>Method Not Allowed</h1>", status=405)
    if in_maintenance():
        return HttpResponseForbidden(
            _("Sorry, you can’t vote a comment while the server is under maintenance.")
        )
    # current video
    c_video = get_object_or_404(Video, slug=video_slug)
    # current comment
    c = get_object_or_404(Comment, video=c_video, id=comment_id) if comment_id else None
    # current user
    c_user = request.user
    if not c_user:
        return HttpResponse("<h1>Bad Request</h1>", status=400)
    response = {}
    # get vote on current comment
    c_vote = Vote.objects.filter(user=c_user, comment=c, comment__video=c_video).first()
    if c_vote:
        c_vote.delete()
        response["voted"] = False
    else:
        c_vote = Vote()
        c_vote.comment = c
        c_vote.user = c_user
        c_vote.save()
        response["voted"] = True

    return HttpResponse(json.dumps(response), content_type="application/json")


@ajax_login_required
@csrf_protect
def add_comment(request, video_slug, comment_id=None):
    if in_maintenance():
        return HttpResponseForbidden(
            _("Sorry, you can’t comment while the server is under maintenance.")
        )
    if request.method == "POST":
        # current video
        c_video = get_object_or_404(Video, slug=video_slug)
        # current user
        c_user = request.user
        # current comment first parent(direct on video)
        c_direct_parent = (
            get_object_or_404(Comment, id=request.POST.get("direct_parent"))
            if (request.POST.get("direct_parent"))
            else None
        )
        # comment's direct parent
        c_parent = get_object_or_404(Comment, id=comment_id) if comment_id else None
        # comment text
        c_content = request.POST.get("content", "")
        # comment date added
        c_date = request.POST.get("date_added", None)
        if c_content:
            c = Comment()
            if c_direct_parent:
                c.direct_parent = c_direct_parent
            if c_parent:
                c.parent = c_parent
            if c_date:
                c.added = parse(c_date)
            c.video = c_video
            c.content = c_content
            c.author = c_user
            c.save()
            data = {
                "id": c.id,
                "author_name": "{0} {1}".format(c_user.first_name, c_user.last_name),
            }
            return HttpResponse(json.dumps(data), content_type="application/json")
        return HttpResponse("<h1>Bad Request</h1>", status=400)
    return HttpResponseNotFound("<h1>Method Not Allowed</h1>", status=405)


def get_parent_comments(request, video):
    """
    Return only comments without parent.

    (direct comments to video) which contains
    number of votes and children
    """
    parent_comment = (
        Comment.objects.filter(video=video, parent=None)
        .order_by("added")
        .annotate(nbr_vote=Count("vote", distinct=True))
        .annotate(
            author_name=Concat("author__first_name", Value(" "), "author__last_name")
        )
        .annotate(nbr_child=Count("children", distinct=True))
        .annotate(
            is_owner=Case(
                When(author__id=request.user.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            )
        )
        .values(
            "id",
            "author_name",
            "is_owner",
            "content",
            "added",
            "nbr_vote",
            "nbr_child",
        )
    )

    return HttpResponse(
        json.dumps(list(parent_comment), cls=DjangoJSONEncoder),
        content_type="application/json",
    )


def get_children_comment(request, comment_id, video_slug):
    """Return one comment with all children."""
    try:
        v = get_object_or_404(Video, slug=video_slug)
        parent_comment = (
            Comment.objects.filter(video=v, id=comment_id)
            .annotate(
                author_name=Concat("author__first_name", Value(" "), "author__last_name")
            )
            .annotate(nbr_child=Count("children", distinct=True))
            .annotate(
                is_owner=Case(
                    When(author__id=request.user.id, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
            .annotate(nbr_vote=Count("vote"))
            .first()
        )
        if parent_comment is None:
            raise Exception("Error: comment doesn't exist: " + comment_id)

        children = parent_comment.get_json_children(request.user.id)
        parent_comment_data = {
            "id": parent_comment.id,
            "author_name": parent_comment.author_name,
            "is_owner": parent_comment.is_owner,
            "content": parent_comment.content,
            "added": parent_comment.added,
            "nbr_vote": parent_comment.nbr_vote,
            "nbr_child": parent_comment.nbr_child,
            "children": children,
        }
    except Http404:
        return HttpResponse(
            json.dumps({"error": "Comment doesn't exist"}),
            content_type="application/json",
        )

    return HttpResponse(
        json.dumps(parent_comment_data, cls=DjangoJSONEncoder),
        content_type="application/json",
    )


def get_comments(request, video_slug):
    v = get_object_or_404(Video, slug=video_slug)
    filter_type = request.GET.get("only", None)

    # get all direct(parent) comments to a video
    if filter_type and filter_type.lower() == "parents":
        return get_parent_comments(request, v)

    else:  # get all comments with all children
        # extract parent comments
        p_c = (
            Comment.objects.filter(video=v, parent=None)
            .order_by("added")
            .annotate(nbr_vote=Count("vote", distinct=True))
            .annotate(
                author_name=Concat("author__first_name", Value(" "), "author__last_name")
            )
            .annotate(nbr_child=Count("children", distinct=True))
            .annotate(
                is_owner=Case(
                    When(author__id=request.user.id, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            )
        )

        # organize comments => parent with children
        comment_org = []
        for c in p_c:
            children = c.get_json_children(request.user.id)
            parent_comment_data = {
                "id": c.id,
                "author_name": c.author_name,
                "is_owner": c.is_owner,
                "content": c.content,
                "added": c.added,
                "nbr_vote": c.nbr_vote,
                "nbr_child": c.nbr_child,
                "children": children,
            }
            comment_org.append(parent_comment_data)
        return HttpResponse(
            json.dumps(comment_org, cls=DjangoJSONEncoder),
            content_type="application/json",
        )


@ajax_login_required
@csrf_protect
def delete_comment(request, video_slug, comment_id):
    """Delete the comment `comment_id` associated to `video_slug`.

    Args:
        video_slug (string): the video associated to this comment
        comment_id (): id of the comment to be deleted
    Returns:
        HttpResponse
    """
    v = get_object_or_404(Video, slug=video_slug)
    c_user = request.user
    c = get_object_or_404(Comment, video=v, id=comment_id)
    response = {
        "deleted": True,
    }

    if in_maintenance():
        return HttpResponseForbidden(
            _("Sorry, you can’t delete a comment while the server is under maintenance.")
        )

    if c.author == c_user or v.owner == c_user or c_user.is_superuser:
        c.delete()
        response["comment_deleted"] = comment_id
        return HttpResponse(json.dumps(response), content_type="application/json")
    else:
        response["deleted"] = False
        response["message"] = _("You do not have rights to delete this comment")
        return HttpResponse(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )


@login_required(redirect_field_name="referrer")
def get_videos_for_category(request, videos_list: dict, category=None):
    """
    Get paginated videos for category modal.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        videos_list (::class::`django.http.QueryDict`): The video list.
        category (::class::`pod.video.models.Category`): Optional category object.

    Returns:
        Return paginated videos in paginator object.
    """
    cats = Category.objects.prefetch_related("video").filter(owner=request.user)
    videos = videos_list.exclude(category__in=cats)

    if category is not None:
        videos = list(chain(category.video.all(), videos))

    page = request.GET.get("page", 1)

    paginator = Paginator(videos, 12)
    paginated_videos_without_cat = get_paginated_videos(paginator, page)

    return paginated_videos_without_cat


@login_required(redirect_field_name="referrer")
@ajax_required
def get_categories_list(request):
    """
    Get actual categories list for filter_aside elements.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.

    Returns:
        Template of categories list item in filter aside.
    """
    data_context = {}
    categories = Category.objects.prefetch_related("video").filter(owner=request.user)
    data_context["categories"] = categories
    return render(request, "videos/filter_aside_categories_list.html", data_context)


@login_required(redirect_field_name="referrer")
def get_json_videos_categories(request):
    """
    Get categories with associated videos in json object.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.

    Returns:
        Json object with category slug as key and array of video(s) as value.
    """
    categories = Category.objects.prefetch_related("video").filter(owner=request.user)
    all_categories_videos = {}
    for cat in categories:
        videos = list(cat.video.all().values_list("slug", flat=True))
        all_categories_videos[cat.slug] = videos
    return json.dumps(all_categories_videos)


@login_required(redirect_field_name="referrer")
@ajax_required
def add_category(request):
    """
    Add category managment. Get method return datas to fill the modal interface. Post method perform the insert.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.

    Returns:
        ::class::`django.http.HttpResponse`: The HTTP response.
    """
    if request.method == "POST":

        response = {"success": False}
        c_user = request.user

        r_title = request.POST.get("title")
        r_videos = request.POST.get("videos")

        if not r_title or json.loads(r_title) == "":
            response["message"] = _("Title field is required")
            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        if not r_videos:
            response["message"] = _(
                "At least one video must be associated with this category."
            )
            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        title = json.loads(r_title)
        videos_slugs = json.loads(r_videos)
        videos = Video.objects.filter(slug__in=videos_slugs)

        # Constraint, video can be only in one of user's categories
        user_cats = Category.objects.filter(owner=c_user)
        v_already_in_user_cat = videos.filter(category__in=user_cats)

        if v_already_in_user_cat:
            response["message"] = _("One or many videos already have a category.")

            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        try:
            cat = Category.objects.create(title=title, owner=c_user)
            cat.video.add(*videos)
            cat.save()
        except IntegrityError:
            # Cannot duplicate category
            response["message"] = _("A category with the same name already exists.")
            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        response["success"] = True
        response["message"] = _("Category successfully added.")

        return HttpResponse(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )
    else:
        data_context = {}

        videos_list = get_videos_for_owner(request)
        videos = get_videos_for_category(request, videos_list)
        data_context["videos"] = videos

        if request.GET.get("page"):
            return render(request, "videos/category_modal_video_list.html", data_context)

        data_context = {
            "modal_action": "add",
            "modal_title": _("Add new category"),
            "videos": videos,
        }
        return render(request, "videos/category_modal.html", data_context)


@login_required(redirect_field_name="referrer")
@ajax_required
def edit_category(request, c_slug=None):
    """
    Edit category managment. Get method return datas to fill the modal interface. Post method perform the update.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        c_slug (str): The optionnal category's slug.

    Returns:
        ::class::`django.http.HttpResponse`: The HTTP response.
    """
    if request.method == "POST":
        response = {"success": False}
        c_user = request.user
        cat = get_object_or_404(Category, slug=c_slug)

        r_title = request.POST.get("title")
        r_videos = request.POST.get("videos")

        if not r_title or json.loads(r_title) == "":
            response["message"] = _("Title field is required")
            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        if not r_videos:
            response["message"] = _(
                "At least one video must be associated with this category."
            )
            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        title = json.loads(r_title)
        videos_slugs = json.loads(r_videos)
        new_videos = Video.objects.filter(slug__in=videos_slugs)

        # Constraint, video can be only in one of user's categories,
        # except current category
        user_cats = Category.objects.filter(owner=c_user).exclude(id=cat.id)
        v_already_in_user_cat = new_videos.filter(category__in=user_cats)
        if v_already_in_user_cat:
            response["message"] = _("One or many videos already have a category.")

            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        if c_user == cat.owner or c_user.is_superuser:
            try:
                cat.title = title
                cat.video.set(list(new_videos))
                cat.save()

                response["success"] = True
                response["message"] = _("Category updated successfully.")
                response["all_categories_videos"] = get_json_videos_categories(request)

                return HttpResponse(
                    json.dumps(response, cls=DjangoJSONEncoder),
                    content_type="application/json",
                )
            except IntegrityError:
                response["message"] = _("A category with the same name already exists.")

                return HttpResponseBadRequest(
                    json.dumps(response, cls=DjangoJSONEncoder),
                    content_type="application/json",
                )

        response["message"] = _("You do not have rights to edit this category")
        return HttpResponseForbidden(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )
    else:
        category = get_object_or_404(Category, slug=c_slug, owner=request.user)
        category_videos = list(category.video.all().values_list("id", flat=True))

        videos_list = get_videos_for_owner(request)
        videos = get_videos_for_category(request, videos_list, category)

        if request.GET.get("page"):
            return render(
                request,
                "videos/category_modal_video_list.html",
                {
                    "videos": videos,
                    "category_videos": category_videos,
                },
            )

        data_context = {
            "modal_action": "edit",
            "modal_title": _("Edit category") + " " + category.title,
            "videos": videos,
            "category": category,
            "category_videos": category_videos,
        }
    return render(request, "videos/category_modal.html", data_context)


@login_required(redirect_field_name="referrer")
@ajax_required
def delete_category(request, c_slug):
    """
    Delete category managment. Get method return datas to fill the modal interface. Post method perform the deletion.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        c_slug (str): The category's slug.

    Returns:
        ::class::`django.http.HttpResponse`: The HTTP response.
    """
    if request.method == "POST":
        response = {"success": False}
        c_user = request.user  # connected user
        cat = get_object_or_404(Category, slug=c_slug)

        if cat.owner == c_user:
            response["id"] = cat.id
            response["videos"] = list(
                map(
                    lambda v: {
                        "slug": v.slug,
                        "title": v.title,
                        "duration": v.duration_in_time,
                        "thumbnail": v.get_thumbnail_card(),
                        "is_video": v.is_video,
                    },
                    cat.video.all(),
                )
            )

            cat.delete()
            response["success"] = True
            response["message"] = _("Category successfully deleted.")

            return HttpResponse(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        response["message"] = _("You do not have rights to delete this category")

        return HttpResponseForbidden(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )
    else:
        category = get_object_or_404(Category, slug=c_slug, owner=request.user)

        data_context = {
            "modal_action": "delete",
            "modal_title": _("Delete category") + " " + category.title,
            "category": category,
        }
    return render(request, "videos/category_modal.html", data_context)


class PodChunkedUploadView(ChunkedUploadView):
    model = ChunkedUpload
    field_name = "the_file"

    def check_permissions(self, request):
        if not request.user.is_authenticated:
            return False
        elif RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
            return False
        pass


class PodChunkedUploadCompleteView(ChunkedUploadCompleteView):
    model = ChunkedUpload
    slug = ""

    def check_permissions(self, request):
        if not request.user.is_authenticated:
            return False
        elif RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
            return False
        pass

    def on_completion(self, uploaded_file, request) -> None:
        """Triggered when a chunked upload is complete."""
        edit_slug = request.POST.get("slug")
        transcript = request.POST.get("transcript", "")
        if edit_slug == "":
            video = Video.objects.create(
                video=uploaded_file,
                owner=request.user,
                type=Type.objects.get(id=DEFAULT_TYPE_ID),
                title=uploaded_file.name,
                transcript=transcript,
            )
        else:
            video = Video.objects.get(slug=edit_slug)
            video.video = uploaded_file
            video.transcript = transcript
        video.launch_encode = True
        video.save()
        self.slug = video.slug
        pass

    def get_response_data(self, chunked_upload, request):
        return {
            "redirlink": reverse("video:video_edit", args=(self.slug,)),
            "message": (
                "You successfully uploaded '%s' (%s bytes)!"
                % (chunked_upload.filename, chunked_upload.offset)
            ),
        }


@csrf_protect
@login_required(redirect_field_name="referrer")
@admin_required
def update_video_owner(request, user_id: int) -> JsonResponse:
    """
    Update video owner.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        user_id (int): User identifier.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response.
    """
    if request.method == "POST":
        post_data = json.loads(request.body.decode("utf-8"))

        videos = post_data.get("videos", [])
        owner_id = post_data.get("owner", 0)
        response = {"success": True, "detail": _("Update successfully")}
        if 0 in (owner_id, len(videos)):
            return JsonResponse(
                {
                    "success": False,
                    "detail": "Bad request: Please one or more fields are invalid",
                },
                safe=False,
            )

        old_owner = User.objects.filter(pk=user_id).first()
        new_owner = User.objects.filter(pk=owner_id).first()

        if None in (old_owner, new_owner):
            return JsonResponse(
                {"success": False, "detail": "New owner or Old owner does not exist"},
                safe=False,
            )

        one_or_more_not_updated = False
        with futures.ThreadPoolExecutor() as executor:
            for v in videos:
                res = executor.submit(change_owner, v, new_owner).result()
                if res is False:
                    one_or_more_not_updated = True

        if one_or_more_not_updated:
            return JsonResponse(
                {**response, "detail": "One or more videos not updated"}, safe=False
            )

        return JsonResponse(response, safe=False)

    return JsonResponse(
        {"success": False, "detail": "Method not allowed: Please use post method"},
        safe=False,
    )


@login_required(redirect_field_name="referrer")
@admin_required
def filter_owners(request):
    try:
        limit = int(request.GET.get("limit", 12))
        offset = int(request.GET.get("offset", 0))
        search = request.GET.get("q", "")
        return auth_get_owners(search, limit, offset)

    except Exception as err:
        return JsonResponse({"success": False, "detail": "Syntax error: {0}".format(err)})


@login_required(redirect_field_name="referrer")
@admin_required
def filter_videos(request, user_id):
    try:
        limit = int(request.GET.get("limit", 12))
        offset = int(request.GET.get("offset", 0))
        title = request.GET.get("title", None)
        search = request.GET.get("q", None)
        return video_get_videos(title, user_id, search, limit, offset)

    except Exception as err:
        return JsonResponse({"success": False, "detail": "Syntax error: {0}".format(err)})


def get_serialized_channels(request: WSGIRequest, channels: QueryDict) -> dict:
    """
    Get serialized channels.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        channels (::class::`django.http.QueryDict`): The channel list.
    Returns:
        dict: The channel list in JSON format.
    """
    channels_json_format = {}
    for num, channel in enumerate(channels):
        channels_json_format[num] = ChannelSerializer(
            channel, context={"request": request}
        ).data
        channels_json_format[num]["url"] = reverse(
            "channel-video:channel", kwargs={"slug_c": channel.slug}
        )
        channels_json_format[num]["videoCount"] = channel.video_count
        channels_json_format[num]["headbandImage"] = (
            channel.headband.file.url if channel.headband else ""
        )
        channels_json_format[num]["themes"] = channel.themes.count()
    return channels_json_format


def get_channel_tabs_for_navbar(request: WSGIRequest) -> JsonResponse:
    """
    Get the channel tabs for the navbar.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response.
    """
    channel_tabs = AdditionalChannelTab.objects.all()
    channel_tabs_json_format = {}
    for num, channel_tab in enumerate(channel_tabs):
        channel_tabs_json_format[num] = {
            "id": channel_tab.pk,
            "name": channel_tab.name,
        }
    return JsonResponse(channel_tabs_json_format, safe=False)


def get_channels_for_specific_channel_tab(request: WSGIRequest) -> JsonResponse:
    """
    Get the channels for a specific channel tab.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response.
    """
    page_number = request.GET.get("page", 1)
    channel_tab_id = request.GET.get("id")
    if channel_tab_id:
        channels = (
            Channel.objects.filter(
                visible=True,
                video__is_draft=False,
                add_channels_tab=channel_tab_id,
                site=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
            .order_by("title")
        )
    else:
        channels = (
            Channel.objects.filter(
                visible=True,
                video__is_draft=False,
                add_channels_tab=None,
                site=get_current_site(request),
            )
            .distinct()
            .annotate(video_count=Count("video", distinct=True))
            .order_by("title")
        )
    paginator = Paginator(channels, CHANNELS_PER_BATCH)
    page_obj = paginator.get_page(page_number)
    response = {}
    response["channels"] = get_serialized_channels(request, page_obj.object_list)
    response["currentPage"] = page_obj.number
    response["totalPages"] = paginator.num_pages
    response["count"] = len(channels)
    return JsonResponse(response, safe=False)


def get_theme_list_for_specific_channel(request: WSGIRequest, slug: str) -> JsonResponse:
    """
    Get the themes for a specific channel.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        request (`str`): The channel slug.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response.
    """
    channel = Channel.objects.get(slug=slug)
    return JsonResponse(json.loads(channel.get_all_theme_json()), safe=False)


"""
# check access to video
# change template to fix height and breadcrumbs
@csrf_protect
@login_required(redirect_field_name='referrer')
def video_collaborate(request, slug):
    action = None
    if (request.method == 'POST' and request.POST.get('action')):
        action = request.POST.get('action').split('_')[0]
    elif (request.method == 'GET' and request.GET.get('action')):
        action = request.GET.get('action').split('_')[0]
    if action in __NOTE_ACTION__:
        return eval('video_note_{0}(request, slug)'.format(action))
    video = get_object_or_404(
        Video, slug=slug, sites=get_current_site(request))
    listNotes = get_adv_note_list(request, video)
    return render(
            request,
            'videos/video_collaborate.html', {
                'video': video,
                'listNotes': listNotes})
"""
