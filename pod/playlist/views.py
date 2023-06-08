from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.http import Http404, HttpResponseBadRequest
from django.db import transaction

from pod.main.utils import is_ajax
from pod.main.views import in_maintenance
from pod.video.models import Video
from .models import Playlist, PlaylistContent
from pod.video.utils import sort_videos_list
from .forms import PlaylistForm, PlaylistRemoveForm
import json

from .utils import (
    get_playlist,
    get_playlist_list_for_user,
    get_public_playlist,
    get_video_list_for_playlist,
    remove_playlist,
    user_add_video_in_playlist,
    user_remove_video_from_playlist,
)

from pod.video.views import CURSUS_CODES, get_owners_has_instances




@login_required(redirect_field_name="referrer")
def playlist_list(request):
    """Render playlists page."""
    visibility = request.GET.get("visibility", "all")
    if visibility in ["private", "protected", "public"]:
        playlists = get_playlist_list_for_user(request.user).filter(visibility=visibility)
    elif visibility == "allpublic":
        playlists = get_public_playlist()
    elif visibility == "allmy":
        playlists = get_playlist_list_for_user(request.user)
    elif visibility == "all":
        playlists = (get_playlist_list_for_user(request.user) | get_public_playlist())
    else:
        return redirect(reverse('playlist:list'))
    return render(
        request,
        "playlist/playlists.html",
        {
            "page_title": _("Playlists"),
            "playlists": playlists,
        }
    )


@login_required(redirect_field_name="referrer")
def playlist_content(request, slug):
    """Render the videos list of a playlist."""
    sort_field = request.GET.get("sort", "rank")
    sort_direction = request.GET.get("sort_direction")
    playlist = get_playlist(slug)
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

    ownersInstances = get_owners_has_instances(request.GET.getlist("owner"))

    if is_ajax(request):
        return render(
            request,
            "playlist/playlist-videos-list.html",
            {"videos": videos, "playlist": playlist, "full_path": full_path, "count_videos": count_videos},
        )

    return render(
        request,
        "playlist/playlist.html",
        {
            "page_title": _("Playlist") + " : " + playlist.name,
            "videos": videos,
            "playlist": playlist,
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
            "sort_direction": sort_direction,
        },
    )


def remove_video_in_playlist(request, slug, video_slug):
    """Remove a video in playlist."""
    playlist = get_object_or_404(Playlist, slug=slug)
    video = Video.objects.get(slug=video_slug)
    user_remove_video_from_playlist(playlist, video)
    return redirect(request.META["HTTP_REFERER"])


def add_video_in_playlist(request, slug, video_slug):
    """Add a video in playlist."""
    playlist = get_playlist(slug)
    video = Video.objects.get(slug=video_slug)
    user_add_video_in_playlist(playlist, video)
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
        {"playlist": playlist, "form": form, "page_title": f"{_('Delete the playlist')} \"{playlist.name}\""}
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def add_or_edit(request, slug: str=None):
    """Add or edit view with form."""
    options = ""
    page_title = ""
    playlist = get_object_or_404(Playlist, slug=slug) if slug else None
    if in_maintenance():
        return redirect(reverse("maintenance"))
    elif request.method == "POST":
        form = PlaylistForm(request.POST, instance=playlist) if playlist else PlaylistForm(request.POST)
        if form.is_valid():
            # raise Exception(f"request.POST.get('additional_owners'): {request.POST.get('additional_owners')} [{type(request.POST.get('additional_owners'))}]")
            new_playlist = form.save(commit=False) if playlist == None else playlist
            new_playlist.owner = request.user
            new_playlist.save()
            new_playlist.additional_owners.clear()
            new_playlist.save()
            if (request.POST.get("additional_owners")):
                for o in request.POST.get("additional_owners"):
                    new_playlist.additional_owners.add(o)
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
            else:
                return HttpResponseRedirect(
                    reverse("playlist:content", kwargs={"slug": new_playlist.slug})
                )
    elif request.method == "GET":
        if request.GET.get("next"):
            options = f"?next={request.GET.get('next')}"
        playlist = get_object_or_404(Playlist, slug=slug) if slug else None
        if playlist:
            if (request.user == playlist.owner or request.user.is_staff) and playlist.editable:
                form = PlaylistForm(instance=playlist)
                page_title = _("Edit the playlist") + f" \"{playlist.name}\""
            else:
                return redirect(reverse("playlist:list"))
        else:
            form = PlaylistForm()
            page_title = _("Add a playlist")
    return render(request, "playlist/add_or_edit.html", {
        "form": form,
        "page_title": page_title,
        "options": options,
    })

# FAVORITES

@csrf_protect
def favorites_save_reorganisation(request, slug: str):
    """Save reorganization when the user click on save button."""
    if request.method == "POST":
        json_data = request.POST.get("json-data")
        try:
            dict_data = json.loads(json_data)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON au mauvais format")
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
