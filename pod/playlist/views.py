from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.db import transaction

from pod.main.utils import is_ajax
from pod.main.views import in_maintenance
from pod.video.views import CURSUS_CODES, get_owners_has_instances
from pod.video.models import Video
from pod.video.utils import sort_videos_list

from .models import Playlist, PlaylistContent
from .forms import PlaylistForm, PlaylistPasswordForm, PlaylistRemoveForm
from pod.playlist.templatetags.favorites_playlist import get_playlist_name
from .utils import (
    check_password,
    get_additional_owners,
    get_favorite_playlist_for_user,
    get_link_to_start_playlist,
    get_playlist,
    get_playlist_list_for_user,
    get_playlists_for_additional_owner,
    get_promoted_playlist,
    get_public_playlist,
    get_video_list_for_playlist,
    remove_playlist,
    sort_playlist_list,
    user_add_video_in_playlist,
    user_remove_video_from_playlist,
)

import json
import hashlib


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


@login_required(redirect_field_name="referrer")
def playlist_list(request):
    """Render playlists page."""
    visibility = request.GET.get("visibility", "all")
    if visibility in ["private", "protected", "public"]:
        playlists = get_playlist_list_for_user(request.user).filter(visibility=visibility)
    elif visibility == "additional":
        playlists = get_playlists_for_additional_owner(request.user)
    elif visibility == "allpublic":
        playlists = get_public_playlist()
    elif visibility == "allmy":
        playlists = get_playlist_list_for_user(request.user)
    elif visibility == "all":
        playlists = (
            get_playlist_list_for_user(request.user)
            | get_public_playlist()
            | get_playlists_for_additional_owner(request.user)
        )
    elif visibility == "promoted":
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


@login_required(redirect_field_name="referrer")
def playlist_content(request, slug):
    """Render the videos list of a playlist."""
    sort_field = request.GET.get("sort", "rank")
    sort_direction = request.GET.get("sort_direction")
    playlist = get_playlist(slug)
    if (
        playlist.visibility == "public"
        or playlist.visibility == "protected"
        or (
            playlist.owner == request.user
            or playlist in get_playlists_for_additional_owner(request.user)
            or request.user.is_staff
        )
    ):
        return render_playlist(request, playlist, sort_field, sort_direction)
    else:
        return HttpResponseRedirect(reverse("playlist:list"))


def render_playlist_page(
    request,
    playlist,
    videos,
    in_favorites_playlist,
    count_videos,
    sort_field,
    sort_direction,
    form=None,
):
    """Render playlist page with the videos list of this."""
    page_title = _("Playlist") + " : " + get_playlist_name(playlist)
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


def toggle_render_playlist_user_has_right(
    request,
    playlist,
    videos,
    in_favorites_playlist,
    count_videos,
    sort_field,
    sort_direction,
):
    """Toggle render_playlist() when the user has right."""
    if request.method == "POST":
        form = PlaylistPasswordForm(request.POST)
        form_password = request.POST.get("password")
        if form_password and check_password(form_password, playlist):
            return render_playlist_page(
                request,
                playlist,
                videos,
                in_favorites_playlist,
                count_videos,
                sort_field,
                sort_direction,
                form,
            )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("The password is incorrect."),
            )
            return redirect(request.META["HTTP_REFERER"])
    else:
        form = PlaylistPasswordForm()
        return render(
            request,
            "playlist/protected-playlist-form.html",
            {
                "form": form,
                "playlist": playlist,
            },
        )


@login_required(redirect_field_name="referrer")
def render_playlist(
    request: dict, playlist: Playlist, sort_field: str, sort_direction: str
):
    """Render playlist page with the videos list of this."""
    videos_list = sort_videos_list(
        get_video_list_for_playlist(playlist), sort_field, sort_direction
    )
    count_videos = len(videos_list)
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

    playlist_url = reverse(
        "playlist:content",
        kwargs={
            "slug": get_favorite_playlist_for_user(request.user).slug,
        },
    )
    in_favorites_playlist = playlist_url == request.path
    if (
        playlist.visibility == "protected"
        and playlist.owner != request.user
        and request.user not in get_additional_owners(playlist)
    ):
        return toggle_render_playlist_user_has_right(
            request,
            playlist,
            videos,
            in_favorites_playlist,
            count_videos,
            sort_field,
            sort_direction,
        )

    if is_ajax(request):
        return render(
            request,
            "playlist/playlist-videos-list.html",
            {
                "videos": videos,
                "playlist": playlist,
                "in_favorites_playlist": in_favorites_playlist,
                "full_path": full_path,
                "count_videos": count_videos,
            },
        )
    return render_playlist_page(
        request,
        playlist,
        videos,
        in_favorites_playlist,
        count_videos,
        sort_field,
        sort_direction,
    )


@login_required(redirect_field_name="referrer")
def remove_video_in_playlist(request, slug, video_slug):
    """Remove a video in playlist."""
    playlist = get_object_or_404(Playlist, slug=slug)
    video = Video.objects.get(slug=video_slug)
    user_remove_video_from_playlist(playlist, video)
    if request.GET.get("json"):
        return JsonResponse(
            {
                "state": "out-playlist",
            }
        )
    return redirect(request.META["HTTP_REFERER"])


@login_required(redirect_field_name="referrer")
def add_video_in_playlist(request, slug, video_slug):
    """Add a video in playlist."""
    playlist = get_playlist(slug)
    video = Video.objects.get(slug=video_slug)
    user_add_video_in_playlist(playlist, video)
    if request.GET.get("json"):
        return JsonResponse(
            {
                "state": "in-playlist",
            }
        )
    return redirect(request.META["HTTP_REFERER"])


@login_required(redirect_field_name="referrer")
def remove_playlist_view(request, slug: str):
    """Remove playlist with form."""
    playlist = get_object_or_404(Playlist, slug=slug)
    if in_maintenance():
        return redirect(reverse("maintenance"))
    elif request.method == "POST":
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
def handle_post_request_for_add_or_edit_function(request, playlist: Playlist) -> None:
    """Handle post request for add_or_edit function."""
    page_title = ""
    form = (
        PlaylistForm(request.POST, instance=playlist)
        if playlist
        else PlaylistForm(request.POST)
    )
    if playlist:
        page_title = _("Edit the playlist “%(pname)s”") % {"pname": playlist.name}
    else:
        page_title = _("Add a playlist")

    if form.is_valid():
        new_playlist = form.save(commit=False) if playlist is None else playlist
        new_playlist.site = get_current_site(request)
        new_playlist.owner = request.user
        password = request.POST.get("password")
        if password:
            hashed_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
            new_playlist.password = hashed_password

        new_playlist.save()
        new_playlist.additional_owners.clear()
        new_playlist.save()
        if request.POST.get("additional_owners"):
            new_playlist.additional_owners.set(request.POST.getlist("additional_owners"))
            new_playlist.save()
        if request.GET.get("next"):
            video_slug = request.GET.get("next").split("/")[2]
            user_add_video_in_playlist(new_playlist, Video.objects.get(slug=video_slug))
            messages.add_message(
                request,
                messages.INFO,
                _("The playlist has been created and the video has been added in it."),
            )
            return redirect(request.GET.get("next"))
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
def handle_get_request_for_add_or_edit_function(request, slug: str) -> None:
    """Handle get request for add_or_edit function."""
    if request.GET.get("next"):
        options = f"?next={request.GET.get('next')}"
    else:
        options = ""
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    if playlist:
        if (
            request.user == playlist.owner
            or request.user.is_staff
            or request.user in get_additional_owners(playlist)
        ) and playlist.editable:
            form = PlaylistForm(instance=playlist)
            page_title = _("Edit the playlist") + f' "{playlist.name}"'
        else:
            return redirect(reverse("playlist:list"))
    else:
        form = PlaylistForm()
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
def add_or_edit(request, slug: str = None):
    """Add or edit view with form."""
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    if in_maintenance():
        return redirect(reverse("maintenance"))
    elif request.method == "POST":
        return handle_post_request_for_add_or_edit_function(request, playlist)
    elif request.method == "GET":
        return handle_get_request_for_add_or_edit_function(request, slug)


@csrf_protect
@login_required(redirect_field_name="referrer")
def favorites_save_reorganisation(request, slug: str):
    """Save reorganization when the user click on save button."""
    if request.method == "POST":
        json_data = request.POST.get("json-data")
        try:
            dict_data = json.loads(json_data)
        except json.JSONDecodeError:
            return HttpResponseBadRequest(_("JSON in wrong format"))
        with transaction.atomic():
            for videos_tuple in dict_data.values():
                playlist_video_1 = PlaylistContent.objects.filter(
                    playlist=get_playlist(slug),
                    video_id=Video.objects.only("id").get(slug=videos_tuple[0]).id,
                )
                playlist_video_2 = PlaylistContent.objects.filter(
                    playlist=get_playlist(slug),
                    video_id=Video.objects.only("id").get(slug=videos_tuple[1]).id,
                )

                with transaction.atomic():
                    video_1_rank = playlist_video_1[0].rank
                    video_2_rank = playlist_video_2[0].rank
                    playlist_video_1.update(rank=video_2_rank)
                    playlist_video_2.update(rank=video_1_rank)

        return redirect(request.META["HTTP_REFERER"])
    else:
        raise Http404()


def start_playlist(request, slug, video=None):
    playlist = get_object_or_404(Playlist, slug=slug)

    if (
        playlist.visibility == "public"
        or playlist.owner == request.user
        or request.user in get_additional_owners(playlist)
    ):
        return redirect(get_link_to_start_playlist(request, playlist, video))
    elif playlist.visibility == "protected":
        if request.method == "POST":
            form = PlaylistPasswordForm(request.POST)
            form_password = request.POST.get("password")
            if form_password and check_password(form_password, playlist):
                return redirect(get_link_to_start_playlist(request, playlist, video))
            else:
                messages.add_message(
                    request, messages.ERROR, _("The password is incorrect.")
                )
                return redirect(request.META["HTTP_REFERER"])
        else:
            form = PlaylistPasswordForm()
            return render(
                request,
                "playlist/protected-playlist-form.html",
                {
                    "form": form,
                    "playlist": playlist,
                },
            )
    else:
        return redirect(reverse("playlist:list"))


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
    videos = get_video_list_for_playlist(playlist)
    if video in get_video_list_for_playlist(playlist):
        context = {
            "video": video,
            "playlist_in_get": playlist,
            "videos": videos,
        }
        breadcrumbs = render_to_string(
            "playlist/playlist_breadcrumbs.html", context, request
        )
        opengraph = render_to_string("videos/video_opengraph.html", context, request)
        more_script = '<div id="more-script">%s</div>' % render_to_string(
            "videos/video_more_script.html", context, request
        )
        page_aside = render_to_string("videos/video_page_aside.html", context, request)
        page_content = render_to_string(
            "videos/video_page_content.html", context, request
        )
        page_title = "<title>%s - %s</title>" % (
            __TITLE_SITE__,
            render_to_string("videos/video_page_title.html", context, request),
        )
        response_data = {
            "breadcrumbs": breadcrumbs,
            "opengraph": opengraph,
            "more_script": more_script,
            "page_aside": page_aside,
            "page_content": page_content,
            "page_title": page_title,
        }
    else:
        response_data = {
            "error_type": 404,
            "error_text": _("This video isn't present in this playlist."),
        }
    return JsonResponse(response_data)
