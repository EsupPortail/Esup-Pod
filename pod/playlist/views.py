"""Esup-Pod playlist views."""

from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import Paginator
from django.urls import Resolver404, resolve, reverse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.http import (
    Http404,
    HttpResponseBadRequest,
    JsonResponse,
    HttpResponseRedirect,
)
from django.utils.http import url_has_allowed_host_and_scheme

from pod.main.utils import is_ajax
from pod.main.views import in_maintenance
from pod.video.views import CURSUS_CODES, get_owners_has_instances
from pod.video.models import Video
from pod.video.utils import sort_videos_list

from .models import Playlist
from .forms import PlaylistForm, PlaylistRemoveForm
from pod.playlist.templatetags.favorites_playlist import get_playlist_name
from .utils import (
    get_additional_owners,
    get_favorite_playlist_for_user,
    get_link_to_start_playlist,
    get_playlist_list_for_user,
    get_playlists_for_additional_owner,
    get_promoted_playlist,
    get_public_playlist,
    get_video_list_for_playlist,
    remove_playlist,
    sort_playlist_list,
    user_add_video_in_playlist,
    user_remove_video_from_playlist,
    playlist_can_be_displayed,
    require_playlist_access,
    reorganize_playlist,
    user_can_manage_playlist,
    user_can_delete_playlist,
    user_can_see_playlist_video,
)

import json

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

USE_PROMOTED_PLAYLIST = getattr(settings, "USE_PROMOTED_PLAYLIST", False)

ALLOWED_HOSTS = getattr(settings, "ALLOWED_HOSTS", ["pod.localhost"])


def playlist_list(request: WSGIRequest):
    """Render playlists page."""
    visibility = request.GET.get("visibility", "all")
    if visibility in {"private", "protected", "public"} and request.user.is_authenticated:
        playlists = get_playlist_list_for_user(request.user).filter(visibility=visibility)
    elif visibility == "additional" and request.user.is_authenticated:
        playlists = get_playlists_for_additional_owner(request.user)
    elif visibility == "allpublic" and request.user.is_authenticated:
        playlists = get_public_playlist()
    elif visibility == "allmy" and request.user.is_authenticated:
        playlists = get_playlist_list_for_user(request.user)
    elif visibility == "all" and request.user.is_authenticated:
        playlists = (
            get_playlist_list_for_user(request.user)
            | get_public_playlist()
            | get_playlists_for_additional_owner(request.user)
        )
    elif (
        visibility == "promoted" and USE_PROMOTED_PLAYLIST
    ) or not request.user.is_authenticated:
        playlists = get_promoted_playlist()
    else:
        return redirect(reverse("playlist:list"))

    sort_field = request.GET.get("sort")
    sort_direction = request.GET.get("sort_direction")

    playlists = sort_playlist_list(playlists, sort_field, sort_direction)

    return render(
        request,
        "playlist/playlists.html",
        {
            "page_title": _("Playlists"),
            "playlists": playlists,
            "sort_field": sort_field,
            "sort_direction": sort_direction,
        },
    )


def playlist_content(request: WSGIRequest, slug: str):
    """Render playlist contents after checking access and any required password."""
    playlist = get_object_or_404(Playlist, slug=slug)
    password_response = require_playlist_access(request, playlist)
    if password_response is not None:
        return password_response
    sort_field = request.GET.get("sort", "rank")
    sort_direction = request.GET.get(
        "sort_direction", "on" if "sort" not in request.GET else ""
    )
    return render_playlist(request, playlist, sort_field, sort_direction)


def render_playlist_page(
    request: WSGIRequest,
    playlist: Playlist,
    videos: list[Video],
    in_favorites_playlist: bool,
    count_videos: int,
    sort_field: str,
    sort_direction: str = None,
    form=None,
):
    """Render playlist page with the videos list of this."""
    page_title = _("Playlist: %(name)s") % {"name": get_playlist_name(playlist)}
    types = request.GET.getlist("type")
    owners = request.GET.getlist("owner")
    disciplines = request.GET.getlist("discipline")
    tags_slug = request.GET.getlist("tag")
    cursus_selected = request.GET.getlist("cursus")
    additional_owners = get_additional_owners(playlist)
    full_path = (
        request.get_full_path()
        .replace("?page=%s" % request.GET.get("page", 1), "")
        .replace("&page=%s" % request.GET.get("page", 1), "")
    )
    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))
    cursus_list = CURSUS_CODES
    sort_field = sort_field
    sort_direction = sort_direction

    context = {
        "page_title": page_title,
        "videos": videos,
        "playlist": playlist,
        "in_favorites_playlist": in_favorites_playlist,
        "count_videos": count_videos,
        "types": types,
        "owners": owners,
        "disciplines": disciplines,
        "tags_slug": tags_slug,
        "cursus_selected": cursus_selected,
        "additional_owners": additional_owners,
        "full_path": full_path,
        "ownersInstances": ownersInstances,
        "cursus_list": cursus_list,
        "sort_field": sort_field,
        "sort_direction": sort_direction,
        "form": form,
    }
    return render(request, "playlist/playlist.html", context)


def render_playlist(
    request: WSGIRequest, playlist: Playlist, sort_field: str, sort_direction: str
):
    """Render playlist contents as a page or an AJAX fragment, including favorites."""
    videos_list = sort_videos_list(
        get_video_list_for_playlist(playlist, prefetch_access=True),
        sort_field,
        sort_direction,
    )
    paginator = Paginator(videos_list, 12)
    videos = paginator.get_page(request.GET.get("page", 1))
    in_favorites_playlist = (
        request.user.is_authenticated
        and playlist == get_favorite_playlist_for_user(request.user)
    )
    if is_ajax(request):
        params = request.GET.copy()
        params.pop("page", None)
        full_path = request.path + (f"?{params.urlencode()}" if params else "")
        return render(
            request,
            "playlist/playlist-videos-list.html",
            {
                "videos": videos,
                "playlist": playlist,
                "in_favorites_playlist": in_favorites_playlist,
                "full_path": full_path,
                "count_videos": paginator.count,
            },
        )
    return render_playlist_page(
        request,
        playlist,
        videos,
        in_favorites_playlist,
        paginator.count,
        sort_field,
        sort_direction,
    )


@login_required(redirect_field_name="referrer")
@require_POST
@csrf_protect
def remove_video_in_playlist(request: WSGIRequest, slug: str, video_slug: str):
    """Remove a video in playlist."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if not user_can_manage_playlist(request.user, playlist):
        raise PermissionDenied
    video = get_object_or_404(Video, slug=video_slug)
    user_remove_video_from_playlist(playlist, video)
    if request.GET.get("json"):
        return JsonResponse(
            {
                "state": "out-playlist",
            }
        )
    referer = request.headers.get("referer", "/")
    if url_has_allowed_host_and_scheme(referer, allowed_hosts=ALLOWED_HOSTS):
        return redirect(referer)
    else:
        return redirect("/")


@login_required(redirect_field_name="referrer")
@require_POST
@csrf_protect
def add_video_in_playlist(request: WSGIRequest, slug: str, video_slug: str):
    """Add a video in playlist."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if not user_can_manage_playlist(request.user, playlist):
        raise PermissionDenied
    video = get_object_or_404(Video, slug=video_slug)
    user_add_video_in_playlist(playlist, video)
    if request.GET.get("json"):
        return JsonResponse(
            {
                "state": "in-playlist",
            }
        )
    referer = request.headers.get("referer", "/")
    if url_has_allowed_host_and_scheme(referer, allowed_hosts=ALLOWED_HOSTS):
        return redirect(referer)
    else:
        return redirect("/")


@login_required(redirect_field_name="referrer")
def remove_playlist_view(request: WSGIRequest, slug: str):
    """Remove playlist with form."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if in_maintenance():
        return redirect(reverse("maintenance"))
    if not user_can_delete_playlist(request.user, playlist):
        raise PermissionDenied
    if request.method == "POST":
        form = PlaylistRemoveForm(request.POST)
        if form.is_valid():
            remove_playlist(request.user, playlist)
            messages.add_message(
                request,
                messages.INFO,
                _("The playlist has been deleted."),
            )
            return redirect(reverse("playlist:list"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    else:
        form = PlaylistRemoveForm()
    return render(
        request,
        "playlist/delete.html",
        {
            "playlist": playlist,
            "form": form,
            "page_title": f"{_('Delete the playlist')} \"{playlist.name}\"",
        },
    )


@login_required(redirect_field_name="referrer")
def handle_post_request_for_add_or_edit_function(
    request: WSGIRequest, playlist: Playlist
):
    """Handle post request for add_or_edit function."""
    page_title = ""
    form = (
        PlaylistForm(request.POST, instance=playlist, user=request.user)
        if playlist
        else PlaylistForm(request.POST, user=request.user)
    )
    if playlist:
        page_title = _("Edit the playlist “%(pname)s”") % {"pname": playlist.name}
    else:
        page_title = _("Add a playlist")

    if form.is_valid():
        new_playlist = form.save(commit=False)
        if playlist is None:
            new_playlist.site = get_current_site(request)
            new_playlist.owner = request.user
        new_playlist.save()
        form.save_m2m()
        next_url = request.GET.get("next")
        is_safe_next_url = bool(
            next_url
            and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            )
        )
        try:
            next_match = resolve(urlsplit(next_url).path) if is_safe_next_url else None
        except Resolver404:
            next_match = None
        is_safe_video_url = next_match and next_match.view_name == "video:video"
        if is_safe_video_url:
            video_slug = next_match.kwargs["slug"]
            user_add_video_in_playlist(new_playlist, Video.objects.get(slug=video_slug))
            messages.add_message(
                request,
                messages.INFO,
                _("The playlist has been created and the video has been added in it."),
            )
            return redirect(next_url)
        return HttpResponseRedirect(
            reverse("playlist:content", kwargs={"slug": new_playlist.slug})
        )
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("The data sent to create the playlist are invalid."),
        )
    return render(
        request,
        "playlist/add_or_edit.html",
        {
            "form": form,
            "page_title": page_title,
            "options": "",
        },
    )


@login_required(redirect_field_name="referrer")
def handle_get_request_for_add_or_edit_function(request: WSGIRequest, slug: str) -> None:
    """Handle get request for add_or_edit function."""
    if request.GET.get("next"):
        options = f"?next={request.GET.get('next')}"
    else:
        options = ""
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    if playlist:
        form = PlaylistForm(instance=playlist, user=request.user)
        page_title = _("Edit playlist “%(name)s”") % {"name": playlist.name}
    else:
        form = PlaylistForm(user=request.user)
        page_title = _("Add a playlist")
    return render(
        request,
        "playlist/add_or_edit.html",
        {
            "form": form,
            "page_title": page_title,
            "options": options,
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def add_or_edit(request: WSGIRequest, slug: str = None):
    """Add or edit view with form."""
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    if in_maintenance():
        return redirect(reverse("maintenance"))
    if playlist and (
        not playlist.editable or not user_can_manage_playlist(request.user, playlist)
    ):
        raise PermissionDenied
    if request.method == "POST":
        return handle_post_request_for_add_or_edit_function(request, playlist)
    elif request.method == "GET":
        return handle_get_request_for_add_or_edit_function(request, slug)


@csrf_protect
@login_required(redirect_field_name="referrer")
def favorites_save_reorganisation(request: WSGIRequest, slug: str):
    """Save reorganization when the user click on save button."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if not user_can_manage_playlist(request.user, playlist):
        raise PermissionDenied
    if request.method == "POST":
        try:
            swaps = json.loads(request.POST.get("json-data", ""))
            if not isinstance(swaps, dict):
                raise ValueError("Reorganization data must be an object")
            reorganize_playlist(playlist, swaps)
        except (ValueError, TypeError, KeyError):
            return HttpResponseBadRequest(_("JSON in wrong format"))

        referer = request.headers.get("referer", "/")
        if url_has_allowed_host_and_scheme(referer, allowed_hosts=ALLOWED_HOSTS):
            return redirect(referer)
        else:
            return redirect("/")
    else:
        raise Http404()


def start_playlist(request: WSGIRequest, slug: str, video: str | None = None):
    """Start an accessible playlist, requesting its password when needed."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if playlist.visibility == "private" and not user_can_manage_playlist(
        request.user, playlist
    ):
        return redirect("playlist:list")
    password_response = require_playlist_access(request, playlist)
    if password_response is not None:
        return password_response
    if video:
        selected_video = get_object_or_404(
            Video, slug=video, playlistcontent__playlist=playlist
        )
        if not user_can_see_playlist_video(request, selected_video, playlist):
            raise PermissionDenied
    url = get_link_to_start_playlist(request, playlist, video)
    return redirect(url or reverse("playlist:content", kwargs={"slug": playlist.slug}))


def get_video(request: WSGIRequest, video_slug: str, playlist_slug: str) -> JsonResponse:
    """
    Get the video in a specific playlist.

    Args:
        request (::class::`django.core.handlers.wsgi.WSGIRequest`): The WSGI request.
        video_slug (::class::`str`): The video slug.
        playlist_slug (::class::`str`): The playlist slug.

    Returns:
        ::class::`django.http.JsonResponse`: The JSON response.
    """
    response_data = {}
    video = get_object_or_404(Video, slug=video_slug)
    playlist = get_object_or_404(Playlist, slug=playlist_slug)
    if not playlist_can_be_displayed(
        request, playlist
    ) or not user_can_see_playlist_video(request, video, playlist):
        raise PermissionDenied
    videos = get_video_list_for_playlist(playlist, prefetch_access=True).order_by("rank")
    if video in videos:
        context = {
            "video": video,
            "playlist_in_get": playlist,
            "videos": videos,
        }
        video_is_enrichment = True if video.get_default_version_link() else False
        templates = {
            "breadcrumbs": "playlist/playlist_breadcrumbs.html",
            "opengraph": "videos/video_opengraph.html",
            "more_script": "enrichment/video_enrichment_more_script.html",
            "page_aside": (
                "enrichment/video_enrichment_page_aside.html"
                if video_is_enrichment
                else "videos/video_page_aside.html"
            ),
            "page_content": (
                "enrichment/video_enrichment_page_content.html"
                if video_is_enrichment
                else "videos/video_page_content.html"
            ),
            "page_title": (
                "enrichment/video_enrichment_page_title.html"
                if video_is_enrichment
                else "videos/video_page_title.html"
            ),
        }
        breadcrumbs = render_to_string(templates["breadcrumbs"], context, request)
        opengraph = render_to_string(templates["opengraph"], context, request)
        more_script = '<div id="more-script">%s</div>' % render_to_string(
            templates["more_script"], context, request
        )
        page_aside = render_to_string(templates["page_aside"], context, request)
        page_content = render_to_string(templates["page_content"], context, request)
        page_title = "<title>%s - %s</title>" % (
            __TITLE_SITE__,
            render_to_string(templates["page_title"], context, request),
        )
        response_data = {
            "breadcrumbs": breadcrumbs,
            "opengraph": opengraph,
            "more_script": more_script,
            "page_aside": page_aside,
            "page_content": page_content,
            "page_title": page_title,
            "enrichment_is_on": video_is_enrichment,
        }
    else:
        response_data = {
            "error_type": 404,
            "error_text": _("This video isn’t present in this playlist."),
        }
    return JsonResponse(response_data)
