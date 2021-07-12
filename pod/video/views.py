from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseNotAllowed, HttpResponseNotFound
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.http import QueryDict, Http404
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, F, Q, Case, When, Value, BooleanField
from django.db.models.functions import Concat
from django.template.loader import render_to_string
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Sum, Min

from dateutil.parser import parse
import concurrent.futures as futures

from pod.main.views import in_maintenance
from pod.main.decorators import ajax_required, admin_required
from pod.authentication.utils import get_owners as auth_get_owners
from pod.video.utils import get_videos as video_get_videos
from pod.video.models import Video
from pod.video.models import Type
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import AdvancedNotes, NoteComments, NOTES_STATUS
from pod.video.models import ViewCount, VideoVersion
from pod.video.models import Comment, Vote, Category
from tagging.models import TaggedItem

from pod.video.forms import VideoForm, VideoVersionForm
from pod.video.forms import ChannelForm
from pod.video.forms import FrontThemeForm
from pod.video.forms import VideoPasswordForm
from pod.video.forms import VideoDeleteForm
from pod.video.forms import AdvancedNotesForm, NoteCommentsForm
from pod.video.utils import pagination_data, get_headband, change_owner

from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
import json
import re
import pandas
from datetime import date
from chunked_upload.models import ChunkedUpload
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView

from pod.playlist.models import Playlist
from django.db import transaction
from django.db import IntegrityError

VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False).defer(
    "video", "slug", "owner", "additional_owners", "description"
)

# for clean install, produces errors
try:
    VIDEOS = VIDEOS.exclude(pk__in=[vid.id for vid in VIDEOS if not vid.encoded]).filter(
        sites=get_current_site(None)
    )
except Exception:
    pass

RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY", False
)
THEME_ACTION = ["new", "modify", "delete", "save"]
NOTE_ACTION = ["get", "save", "remove", "form", "download"]

TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
    "TEMPLATE_VISIBLE_SETTINGS",
    {
        "TITLE_SITE": "Pod",
        "TITLE_ETB": "University name",
        "LOGO_SITE": "img/logoPod.svg",
        "LOGO_ETB": "img/logo_etb.svg",
        "LOGO_PLAYER": "img/logoPod.svg",
        "LINK_PLAYER": "",
        "FOOTER_TEXT": ("",),
        "FAVICON": "img/logoPod.svg",
        "CSS_OVERRIDE": "",
        "PRE_HEADER_TEMPLATE": "",
        "POST_FOOTER_TEMPLATE": "",
        "TRACKING_TEMPLATE": "",
    },
)

TITLE_SITE = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
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

TRANSCRIPT = getattr(settings, "USE_TRANSCRIPTION", False)
VIEW_STATS_AUTH = getattr(settings, "VIEW_STATS_AUTH", False)
ACTIVE_VIDEO_COMMENT = getattr(settings, "ACTIVE_VIDEO_COMMENT", False)
USE_CATEGORY = getattr(settings, "USER_VIDEO_CATEGORY", False)

DEFAULT_RECORDER_TYPE_ID = getattr(settings, "DEFAULT_RECORDER_TYPE_ID", 1)

# ############################################################################
# CHANNEL
# ############################################################################


def _regroup_videos_by_theme(request, videos, channel, theme=None):
    """Regroup videos by theme.\n

    Args:\n
        request (Request): current HTTP Request\n
        videos (List[Video]): list of vidéo filter by channel\n
        channel (Channel): current channel\n
        theme (Theme, optional): current theme. Defaults to None.\n

    Returns:\n
        Dict[str, Any]: json data\n
    """
    target = request.GET.get("target", "").lower()
    limit = int(request.GET.get("limit", 8))
    offset = int(request.GET.get("offset", 0))
    theme_children = None
    parent_title = ""
    response = {}

    if target in ("", "themes"):
        theme_children = Theme.objects.filter(parentId=theme, channel=channel)
        videos = videos.filter(theme=theme, channel=channel)

        if theme is not None and theme.parentId is not None:
            parent_title = theme.parentId.title
        elif theme is not None and theme.parentId is None:
            parent_title = channel.title

    if target in ("", "videos"):
        videos = videos.filter(theme=theme, channel=channel)
        response["next_videos"], *_ = pagination_data(
            request.path, offset, limit, videos.count()
        )
        count = videos.count()
        videos = videos[offset : limit + offset]
        response = {
            **response,
            "videos": list(videos),
            "has_more_videos": (offset + limit) < count,
        }

    if theme_children is not None:
        count_themes = theme_children.count()
        has_more_themes = (offset + limit) < count_themes
        theme_children = theme_children.values("slug", "title")[offset : limit + offset]
        next_url, previous_url, theme_pages_info = pagination_data(
            request.path, offset, limit, count_themes
        )
        response = {
            **response,
            "next": next_url,
            "previous": previous_url,
            "has_more_themes": has_more_themes,
            "count_themes": count_themes,
            "theme_children": list(theme_children),
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
    if request.is_ajax():
        videos = list(
            map(
                lambda v: {
                    "slug": v.slug,
                    "title": v.title,
                    "duration": v.duration_in_time,
                    "thumbnail": v.get_thumbnail_card(),
                    "is_video": v.is_video,
                    "has_password": bool(v.password),
                    "is_restricted": v.is_restricted,
                    "has_chapter": v.chapter_set.all().count() > 0,
                    "is_draft": v.is_draft,
                },
                videos,
            )
        )
        response["videos"] = videos
        return JsonResponse(response, safe=False)

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
    channel = get_object_or_404(Channel, slug=slug_c, sites=get_current_site(request))

    videos_list = VIDEOS.filter(channel=channel)

    theme = None
    if slug_t:
        theme = get_object_or_404(Theme, channel=channel, slug=slug_t)
        list_theme = theme.get_all_children_flat()
        videos_list = videos_list.filter(theme__in=list_theme)

    if getattr(settings, "ORGANIZE_BY_THEME", False):
        return _regroup_videos_by_theme(request, videos_list, channel, theme)

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    videos = paginator(videos_list, page)

    if request.is_ajax():
        return render(
            request,
            "videos/video_list.html",
            {"videos": videos, "full_path": full_path},
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
        .filter(sites=site)
        .annotate(video_count=Count("video", distinct=True))
    )
    return render(request, "channel/my_channels.html", {"channels": channels})


@csrf_protect
@login_required(redirect_field_name="referrer")
def channel_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug, sites=get_current_site(request))
    if request.user not in channel.owners.all() and not (
        request.user.is_superuser or request.user.has_perm("video.change_channel")
    ):
        messages.add_message(request, messages.ERROR, _(u"You cannot edit this channel."))
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
                _(u"One or more errors have been found in the form."),
            )
    return render(request, "channel/channel_edit.html", {"form": channel_form})


# ############################################################################
# THEME EDIT
# ############################################################################


@csrf_protect
@login_required(redirect_field_name="referrer")
def theme_edit(request, slug):
    channel = get_object_or_404(Channel, slug=slug, sites=get_current_site(request))
    if request.user not in channel.owners.all() and not (
        request.user.is_superuser or request.user.has_perm("video.change_theme")
    ):
        messages.add_message(request, messages.ERROR, _(u"You cannot edit this channel."))
        raise PermissionDenied

    if request.POST and request.is_ajax():
        if request.POST["action"] in THEME_ACTION:
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
def my_videos(request):

    data_context = {}
    site = get_current_site(request)
    # Videos list which user is the owner + which user is an additional owner
    videos_list = request.user.video_set.all().filter(
        sites=site
    ) | request.user.owners_videos.all().filter(sites=site)
    videos_list = videos_list.distinct()
    page = request.GET.get("page", 1)

    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    cats = []
    videos_without_cat = []
    if USE_CATEGORY:
        """
        " user's videos categories format =>
        " [{
        " 'title': cat_title,
        " 'slug': cat_slug,
        " 'videos': [v_slug, v_slug...] },]
        """
        cats = Category.objects.prefetch_related("video").filter(owner=request.user)
        videos_without_cat = videos_list.exclude(category__in=cats)
        cats = list(
            map(
                lambda c: {
                    "id": c.id,
                    "title": c.title,
                    "slug": c.slug,
                    "videos": list(c.video.values_list("slug", flat=True)),
                },
                cats,
            )
        )
        cats.insert(0, len(videos_list))
        cats = json.dumps(cats, ensure_ascii=False)
        data_context["categories"] = cats
        data_context["videos_without_cat"] = videos_without_cat

    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request,
            "videos/video_list.html",
            {"videos": videos, "full_path": full_path},
        )
    data_context["use_category"] = USE_CATEGORY
    data_context["videos"] = videos
    data_context["full_path"] = full_path

    return render(request, "videos/my_videos.html", data_context)


def get_videos_list(request):
    videos_list = VIDEOS

    if request.GET.getlist("type"):
        videos_list = videos_list.filter(type__slug__in=request.GET.getlist("type"))
    if request.GET.getlist("discipline"):
        videos_list = videos_list.filter(
            discipline__slug__in=request.GET.getlist("discipline")
        )
    if request.GET.getlist("owner"):
        # Add filter on additional owners
        videos_list = videos_list.filter(
            Q(owner__username__in=request.GET.getlist("owner"))
            | Q(additional_owners__username__in=request.GET.getlist("owner"))
        )
    if request.GET.getlist("tag"):
        videos_list = TaggedItem.objects.get_union_by_model(
            videos_list, request.GET.getlist("tag")
        )
    if request.GET.getlist("cursus"):
        videos_list = videos_list.filter(cursus__in=request.GET.getlist("cursus"))
    return videos_list.distinct()


def get_owners_has_instances(owners):
    ownersInstances = []
    for owner in owners:
        try:
            obj = User.objects.get(username=owner)
            ownersInstances.append(obj)
        except ObjectDoesNotExist:
            pass
    return ownersInstances


def videos(request):
    videos_list = get_videos_list(request)

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)

    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))

    if request.is_ajax():
        return render(
            request,
            "videos/video_list.html",
            {"videos": videos, "full_path": full_path},
        )

    return render(
        request,
        "videos/videos.html",
        {
            "videos": videos,
            "types": request.GET.getlist("type"),
            "owners": request.GET.getlist("owner"),
            "disciplines": request.GET.getlist("discipline"),
            "tags_slug": request.GET.getlist("tag"),
            "cursus_selected": request.GET.getlist("cursus"),
            "full_path": full_path,
            "ownersInstances": ownersInstances,
            "cursus_list": CURSUS_CODES,
        },
    )


def is_in_video_groups(user, video):
    return user.owner.accessgroup_set.filter(
        code_name__in=[
            name[0] for name in video.restrict_access_to_groups.values_list("code_name")
        ]
    ).exists()


def get_video_access(request, video, slug_private):
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
        access_granted_for_draft = request.user.is_authenticated() and (
            request.user == video.owner
            or request.user.is_superuser
            or request.user.has_perm("video.change_video")
            or (request.user in video.additional_owners.all())
        )
        access_granted_for_restricted = (
            request.user.is_authenticated() and not is_restricted_to_group
        )
        access_granted_for_group = (
            (request.user.is_authenticated() and is_in_video_groups(request.user, video))
            or request.user == video.owner
            or request.user.is_superuser
            or request.user.has_perm("recorder.add_recording")
            or (request.user in video.additional_owners.all())
        )

        show_page = (
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
        if show_page:
            return True
        else:
            return False
    else:
        return True


@csrf_protect
def video(request, slug, slug_c=None, slug_t=None, slug_private=None):
    template_video = "videos/video.html"
    params = {"active_video_comment": ACTIVE_VIDEO_COMMENT}
    if request.GET.get("is_iframe"):
        params = {}
        template_video = "videos/video-iframe.html"
    try:
        id = int(slug[: slug.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid video id")

    video = get_object_or_404(Video, id=id, sites=get_current_site(request))
    if video.get_version != "O" and request.GET.get("redirect") != "false":
        return redirect(video.get_default_version_link(slug_private))
    return render_video(request, id, slug_c, slug_t, slug_private, template_video, params)


def render_video(
    request,
    id,
    slug_c=None,
    slug_t=None,
    slug_private=None,
    template_video="videos/video.html",
    more_data={},
):
    video = get_object_or_404(Video, id=id, sites=get_current_site(request))
    """
    # Do it only for video
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
        get_object_or_404(Channel, slug=slug_c, sites=get_current_site(request))
        if slug_c
        else None
    )
    theme = get_object_or_404(Theme, channel=channel, slug=slug_t) if slug_t else None
    playlist = (
        get_object_or_404(Playlist, slug=request.GET["playlist"])
        if request.GET.get("playlist")
        else None
    )
    if playlist and request.user != playlist.owner and not playlist.visible:
        # not (request.user.is_superuser or request.user.has_perm(
        #        "video.change_theme")
        messages.add_message(
            request,
            messages.ERROR,
            _("You don't have access to this playlist."),
        )
        raise PermissionDenied

    is_password_protected = video.password is not None and video.password != ""

    show_page = get_video_access(request, video, slug_private)

    if (
        (show_page and not is_password_protected)
        or (
            show_page
            and is_password_protected
            and request.POST.get("password")
            and request.POST.get("password") == video.password
        )
        or (slug_private and slug_private == video.get_hashkey())
        or request.user == video.owner
        or request.user.is_superuser
        or request.user.has_perm("video.change_video")
        or (request.user in video.additional_owners.all())
    ):
        return render(
            request,
            template_video,
            {
                "channel": channel,
                "video": video,
                "theme": theme,
                "listNotes": listNotes,
                "playlist": playlist,
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
                    "playlist": playlist,
                    "listNotes": listNotes,
                    **more_data,
                },
            )
        elif request.user.is_authenticated():
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
        messages.add_message(request, messages.ERROR, _(u"You cannot edit this video."))
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
                return redirect(reverse("video", args=(video.slug,)))
            else:
                return redirect(reverse("video_edit", args=(video.slug,)))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _(u"One or more errors have been found in the form."),
            )
    return render(request, "videos/video_edit.html", {"form": form})


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

    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))

    if request.user != video.owner and not (
        request.user.is_superuser or request.user.has_perm("video.delete_video")
    ):
        messages.add_message(request, messages.ERROR, _(u"You cannot delete this video."))
        raise PermissionDenied

    form = VideoDeleteForm()

    if request.method == "POST":
        form = VideoDeleteForm(request.POST)
        if form.is_valid():
            video.delete()
            messages.add_message(request, messages.INFO, _("The video has been deleted."))
            return redirect(reverse("my_videos"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _(u"One or more errors have been found in the form."),
            )

    return render(request, "videos/video_delete.html", {"video": video, "form": form})


def get_adv_note_list(request, video):
    """
    Return the list of AdvancedNotes of video
      that can be seen by the current user
    """
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
    Return the list of coms wich are the direct sons of the
      AdvancedNote of id id , that can be seen by the current user
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
    Return a dictionnary build recursively containing
      the list of the direct sons of a com
      for each encountered com
    Starting from the coms present in listComs
    Example, having the next tree of coms :
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
    Return the list of the successive parents of com
      including com from bottom to top
    """
    tree, c = [], com
    while c.parentCom is not None:
        tree.append(c)
        c = c.parentCom
    tree.append(c)
    return tree


def can_edit_or_remove_note_or_com(request, nc, action):
    """
    Check if the current user can apply action to
      the note or comment nc
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
            _(u"You cannot %s this note or comment." % action),
        )
        raise PermissionDenied


def can_see_note_or_com(request, nc):
    """
    Check if the current user can view the note or comment nc
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
            _(u"You cannot see this note or comment."),
        )
        raise PermissionDenied


@csrf_protect
def video_notes(request, slug):
    action = None
    if request.method == "POST" and request.POST.get("action"):
        action = request.POST.get("action").split("_")[0]
    elif request.method == "GET" and request.GET.get("action"):
        action = request.GET.get("action").split("_")[0]
    if action in NOTE_ACTION:
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
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idCom = idNote = None
    if request.method == "POST" and request.POST.get("idCom"):
        idCom = request.POST.get("idCom")
    elif request.method == "GET" and request.GET.get("idCom"):
        idCom = request.GET.get("idCom")
    if request.method == "POST" and request.POST.get("idNote"):
        idNote = request.POST.get("idNote")
    elif request.method == "GET" and request.GET.get("idNote"):
        idCom = request.GET.get("idNote")

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
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idNote, idCom = None, None
    note, com = None, None
    if request.method == "POST" and request.POST.get("idCom"):
        idCom = request.POST.get("idCom")
    elif request.method == "GET" and request.GET.get("idCom"):
        idCom = request.GET.get("idCom")
    if request.method == "POST" and request.POST.get("idNote"):
        idNote = request.POST.get("idNote")
    elif request.method == "GET" and request.GET.get("idNote"):
        idCom = request.GET.get("idNote")

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
    (idNote, idCom, note, com) = params
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
        comToEdit, noteToEdit = com, None
        # Creting a comment answer
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
        comToEdit, noteToEdit = None, None
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
        noteToDisplay, comToDisplay = None, None
        listNotesCom, dictComments = None, None
        comToEdit, noteToEdit = None, note
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
        dictComments = None
        comToEdit, noteToEdit = None, None
    # Creating a note
    elif idCom is None and idNote is None:
        form = AdvancedNotesForm()
        noteToDisplay, comToDisplay = None, None
        listNotesCom, dictComments = None, None
        comToEdit, noteToEdit = None, None

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
    video = get_object_or_404(Video, slug=slug, sites=get_current_site(request))
    idNote, idCom = None, None
    note, com = None, None
    noteToDisplay, comToDisplay = None, None
    noteToEdit, comToEdit = None, None
    listNotesCom, dictComments = None, None
    form = None

    if request.method == "POST" and request.POST.get("idCom"):
        idCom = request.POST.get("idCom")
        com = get_object_or_404(NoteComments, id=idCom)
    if request.method == "POST" and request.POST.get("idNote"):
        idNote = request.POST.get("idNote")
        note = get_object_or_404(AdvancedNotes, id=idNote)

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
        messages.add_message(request, messages.INFO, _("The comment has been saved."))
        noteToDisplay, comToDisplay = note, get_com_tree(com)
        listNotesCom = get_adv_note_com_list(request, idNote)
        dictComments = get_com_coms_dict(request, listNotesCom)
    # Saving a new answer (com) to a com
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
        messages.add_message(request, messages.INFO, _("The note has been saved."))
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
        messages.add_message(request, messages.INFO, _("The comment has been saved."))
        noteToDisplay = note
        listNotesCom = get_adv_note_com_list(request, idNote)
    # Saving a new note
    elif idCom is None and idNote is None:
        note, created = AdvancedNotes.objects.get_or_create(
            user=request.user,
            video=video,
            status=request.POST.get("status"),
            timestamp=request.POST.get("timestamp"),
        )
        if created or not note.note:
            note.note = request.POST.get("note")
        else:
            note.note = note.note + "\n" + request.POST.get("note")
        note.save()
        messages.add_message(request, messages.INFO, _("The note has been saved."))

    return (note, com, noteToDisplay, comToDisplay, listNotesCom, dictComments)


def video_note_form_not_valid(request, params):
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
        _(u"One or more errors have been found in the form."),
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

    def write_to_dict(t, id, s, rn, rc, dc, dm, nt, c):
        contentToDownload["type"].append(t)
        contentToDownload["id"].append(id)
        contentToDownload["status"].append(s)
        contentToDownload["relatedNote"].append(rn)
        contentToDownload["relatedComment"].append(rc)
        contentToDownload["dateCreated"].append(dc)
        contentToDownload["dataModified"].append(dm)
        contentToDownload["noteTimestamp"].append(nt)
        contentToDownload["content"].append(c)

    def rec_expl_coms(idNote, lComs):
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
    video = get_object_or_404(Video, id=id)
    if request.method == "POST":
        try:
            viewCount = ViewCount.objects.get(video=video, date=date.today())
        except ViewCount.DoesNotExist:
            try:
                with transaction.atomic():
                    ViewCount.objects.create(video=video, count=1)
                    return HttpResponse("ok")
            except IntegrityError:
                viewCount = ViewCount.objects.get(video=video, date=date.today())
        viewCount.count = F("count") + 1
        viewCount.save(update_fields=["count"])
        return HttpResponse("ok")
    messages.add_message(request, messages.ERROR, _(u"You cannot access to this view."))
    raise PermissionDenied


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
    messages.add_message(request, messages.ERROR, _(u"You cannot access to this view."))
    raise PermissionDenied


def video_oembed(request):
    if not request.GET.get("url"):
        raise SuspiciousOperation("URL must be specified")
    format = "xml" if request.GET.get("format") == "xml" else "json"

    data = {}
    data["type"] = "video"
    data["version"] = "1.0"
    data["provider_name"] = TITLE_SITE
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

    if m:
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
            reverse("videos"),
            video.owner.username,
        )
        data["html"] = (
            '<iframe src="%(provider)s%(video_url)s%(slug_private)s'
            + '?is_iframe=true" width="640" height="360" '
            + 'style="padding: 0; margin: 0; border:0" '
            + "allowfullscreen loading='lazy'></iframe>"
        ) % {
            "provider": data["provider_url"],
            "video_url": reverse("video", kwargs={"slug": video.slug}),
            "slug_private": "%s/" % slug_private if slug_private else "",
        }
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
        videos = VIDEOS.filter(channel__slug__istartswith=p_slug)

    elif target.lower() == "theme" and p_slug_t:
        title = _("Video viewing statistics for the theme %s") % p_slug_t
        videos = VIDEOS.filter(theme__slug__istartswith=p_slug_t)

    elif target == "videos":
        return (VIDEOS, title)

    return (videos, title)


def view_stats_if_authenticated(user):
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
            {"form": form, "title": page_title},
        )
    elif (
        (not has_rights and video_access_ok and not is_password_protected)
        or (video_access_ok and not is_password_protected)
        or has_rights
    ):
        return render(request, "videos/video_stats_view.html", {"title": page_title})
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
        "The following %(target)s does not " "exist or contain any videos: %(slug)s"
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
        )
    ) or (
        request.method == "GET" and videos and target in ("videos", "channel", "theme")
    ):
        return render(request, "videos/video_stats_view.html", {"title": title})
    else:
        date_filter = request.POST.get("periode", date.today())
        if type(date_filter) == str:
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

        min_date = VIDEOS.aggregate(Min("date_added"))["date_added__min"].date()
        data.append({"min_date": min_date})

        return JsonResponse(data, safe=False)


@login_required(redirect_field_name="referrer")
def video_add(request):
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
            "TRANSCRIPT": TRANSCRIPT,
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


@login_required(redirect_field_name="referrer")
def vote_post(request, video_slug, comment_id):
    if request.method == "GET":
        return HttpResponseNotFound("<h1>Method Not Allowed</h1>", status=405)
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


@login_required(redirect_field_name="referrer")
@csrf_protect
def add_comment(request, video_slug, comment_id=None):
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
    """
    return one comment with all children
    """
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
            raise Exception("Error: comment doesn't exist : " + comment_id)

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


@login_required(redirect_field_name="referrer")
def delete_comment(request, video_slug, comment_id):

    v = get_object_or_404(Video, slug=video_slug)
    c_user = request.user
    c = get_object_or_404(Comment, video=v, id=comment_id)
    response = {
        "deleted": True,
    }

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
@ajax_required
def get_categories(request, c_slug=None):

    response = {"success": False}
    c_user = request.user  # connected user

    # GET method
    if c_slug:  # get category with slug

        cat = get_object_or_404(Category, slug=c_slug)
        response["success"] = True
        response["id"] = cat.id
        response["title"] = cat.title
        response["owner"] = cat.owner.id
        response["slug"] = cat.slug
        response["videos"] = []
        for v in cat.video.all():
            if v.owner == cat.owner or cat.owner in v.additional_owners.all():
                response["videos"].append(
                    {
                        "slug": v.slug,
                        "title": v.title,
                        "duration": v.duration_in_time,
                        "thumbnail": v.get_thumbnail_card(),
                        "is_video": v.is_video,
                        "has_password": bool(v.password),
                        "is_restricted": v.is_restricted,
                        "has_chapter": v.chapter_set.all().count() > 0,
                        "is_draft": v.is_draft,
                    }
                )
            else:
                # delete if user is no longer owner
                # or additional owner of the video
                cat.video.remove(v)

        return HttpResponse(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    else:  # get all categories of connected user

        cats = Category.objects.prefetch_related("video").filter(owner=c_user)
        cats = list(
            map(
                lambda c: {
                    "title": c.title,
                    "slug": c.slug,
                    "videos": list(
                        map(
                            lambda v: {
                                "slug": v.slug,
                                "title": v.title,
                                "duration": v.duration_in_time,
                                "thumbnail": v.get_thumbnail_card(),
                                "is_video": v.is_video,
                                "has_password": bool(v.password),
                                "is_restricted": v.is_restricted,
                                "has_chapter": v.chapter_set.all().count() > 0,
                                "is_draft": v.is_draft,
                            },
                            c.video.all(),
                        )
                    ),
                },
                cats,
            )
        )

        response["success"] = True
        response["categories"] = cats

        return HttpResponse(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )


@login_required(redirect_field_name="referrer")
@ajax_required
def add_category(request):

    response = {"success": False}
    c_user = request.user  # connected user

    if request.method == "POST":  # create new category

        data = json.loads(request.body.decode("utf-8"))

        videos = Video.objects.filter(slug__in=data.get("videos", []))

        # constraint, video can be only in one of user's categories
        user_cats = Category.objects.filter(owner=c_user)
        v_already_in_user_cat = videos.filter(category__in=user_cats)

        if v_already_in_user_cat:
            response["message"] = _("One or many videos already have a category.")

            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        if "title" in data and data["title"].strip() != "":
            try:
                cat = Category.objects.create(title=data["title"], owner=c_user)
                cat.video.add(*videos)
                cat.save()
            except IntegrityError:  # cannot duplicate category
                return HttpResponse(status=409)

            response["category"] = {}
            response["category"]["id"] = cat.id
            response["category"]["title"] = cat.title
            response["category"]["slug"] = cat.slug
            response["success"] = True
            response["category"]["videos"] = list(
                map(
                    lambda v: {
                        "slug": v.slug,
                        "title": v.title,
                        "duration": v.duration_in_time,
                        "thumbnail": v.get_thumbnail_card(),
                        "is_video": v.is_video,
                        "has_password": bool(v.password),
                        "is_restricted": v.is_restricted,
                        "has_chapter": v.chapter_set.all().count() > 0,
                        "is_draft": v.is_draft,
                    },
                    cat.video.all(),
                )
            )

            return HttpResponse(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        response["message"] = _("Title field is required")
        return HttpResponseBadRequest(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    return HttpResponseNotAllowed(_("Method Not Allowed"))


@login_required(redirect_field_name="referrer")
@ajax_required
def edit_category(request, c_slug):

    response = {"success": False}
    c_user = request.user  # connected user

    if request.method == "POST":  # edit current category

        cat = get_object_or_404(Category, slug=c_slug)
        data = json.loads(request.body.decode("utf-8"))

        new_videos = Video.objects.filter(slug__in=data.get("videos", []))

        # constraint, video can be only in one of user's categories,
        # excepte current category
        user_cats = Category.objects.filter(owner=c_user).exclude(id=cat.id)
        v_already_in_user_cat = new_videos.filter(category__in=user_cats)

        if v_already_in_user_cat:
            response["message"] = _("One or many videos already have a category.")

            return HttpResponseBadRequest(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        if "title" in data and data["title"].strip() != "":

            if c_user == cat.owner or c_user.is_superuser:

                cat.title = data["title"]
                cat.video.set(list(new_videos))
                cat.save()
                response["id"] = cat.id
                response["title"] = cat.title
                response["slug"] = cat.slug
                response["success"] = True
                response["message"] = _("Category updated successfully.")
                response["videos"] = list(
                    map(
                        lambda v: {
                            "slug": v.slug,
                            "title": v.title,
                            "duration": v.duration_in_time,
                            "thumbnail": v.get_thumbnail_card(),
                            "is_video": v.is_video,
                            "has_password": bool(v.password),
                            "is_restricted": v.is_restricted,
                            "has_chapter": v.chapter_set.all().count() > 0,
                            "is_draft": v.is_draft,
                        },
                        cat.video.all(),
                    )
                )

                return HttpResponse(
                    json.dumps(response, cls=DjangoJSONEncoder),
                    content_type="application/json",
                )

            response["message"] = _("You do not have rights to edit this category")
            return HttpResponseForbidden(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        response["message"] = _("Title field is required")
        return HttpResponseBadRequest(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    response["message"] = _("Method Not Allowed")
    return HttpResponseNotAllowed(
        json.dumps(response, cls=DjangoJSONEncoder),
        content_type="application/json",
    )


@login_required(redirect_field_name="referrer")
@ajax_required
def delete_category(request, c_id):

    response = {"success": False}
    c_user = request.user  # connected user

    if request.method == "POST":  # create new category

        cat = get_object_or_404(Category, id=c_id)

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

            return HttpResponse(
                json.dumps(response, cls=DjangoJSONEncoder),
                content_type="application/json",
            )

        response["message"] = _("You do not have rights to delete this category")

        return HttpResponseForbidden(
            json.dumps(response, cls=DjangoJSONEncoder),
            content_type="application/json",
        )

    return HttpResponseNotAllowed(_("Method Not Allowed"))


class PodChunkedUploadView(ChunkedUploadView):

    model = ChunkedUpload
    field_name = "the_file"

    def check_permissions(self, request):
        if not request.user.is_authenticated():
            return False
        elif RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
            return False
        pass


class PodChunkedUploadCompleteView(ChunkedUploadCompleteView):

    model = ChunkedUpload
    slug = ""

    def check_permissions(self, request):
        if not request.user.is_authenticated():
            return False
        elif RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
            return False
        pass

    def on_completion(self, uploaded_file, request):
        """Triggered when a chunked upload is complete."""
        edit_slug = request.POST.get("slug")
        transcript = request.POST.get("transcript")
        if edit_slug == "":
            video = Video.objects.create(
                video=uploaded_file,
                owner=request.user,
                type=Type.objects.get(id=1),
                title=uploaded_file.name,
                transcript=(True if (transcript == "true") else False),
            )
        else:
            video = Video.objects.get(slug=edit_slug)
            video.video = uploaded_file
        video.launch_encode = True
        video.save()
        self.slug = video.slug
        pass

    def get_response_data(self, chunked_upload, request):
        return {
            "redirlink": reverse("video_edit", args=(self.slug,)),
            "message": (
                "You successfully uploaded '%s' (%s bytes)!"
                % (chunked_upload.filename, chunked_upload.offset)
            ),
        }


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def video_record(request):
    if in_maintenance():
        return redirect(reverse("maintenance"))
    if RESTRICT_EDIT_VIDEO_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "videos/video_edit.html", {"access_not_allowed": True})
    if request.method == "POST" and request.is_ajax():
        try:
            vid = Video()
            vid.video = request.FILES["video"]
            vid.title = request.POST["title"]
            vid.owner = request.user
            vid.type = Type.objects.get(id=DEFAULT_RECORDER_TYPE_ID)
            vid.save()
            vid.sites.add(get_current_site(request))
            vid.launch_encode = True
            vid.save()
            return JsonResponse(
                {
                    "id": vid.id,
                    "url_edit": reverse("video_edit", args=(vid.slug,)),
                }
            )
        except (RuntimeError, TypeError, NameError, AttributeError) as err:
            return JsonResponse(
                {
                    "error": "Unexpected error: {0}".format(err),
                }
            )
    return render(request, "videos/video_record.html", {})


@csrf_protect
@login_required(redirect_field_name="referrer")
@admin_required
def update_video_owner(request, user_id):
    if request.method == "POST":
        post_data = json.loads(request.body.decode("utf-8"))

        videos = post_data.get("videos", [])
        owner_id = post_data.get("owner", 0)
        response = {"success": True, "detail": "Update successfully"}
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
    if action in NOTE_ACTION:
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
