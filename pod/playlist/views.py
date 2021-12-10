from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from pod.playlist.models import Playlist
from pod.playlist.models import PlaylistElement
from pod.playlist.forms import PlaylistForm
from pod.video.models import Video, AdvancedNotes

import json

ACTION = ["add", "edit", "move", "remove", "delete"]


@login_required(redirect_field_name="referrer")
@csrf_protect
def my_playlists(request):
    playlists = request.user.playlist_set.all()
    page = request.GET.get("page", 1)

    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page={0}".format(page), "")
            .replace("&page={0}".format(page), "")
        )
    paginator = Paginator(playlists, 12)
    try:
        playlists = paginator.page(page)
    except PageNotAnInteger:
        playlists = paginator.page(1)
    except EmptyPage:
        playlists = paginator.page(paginator.num_pages)

    return render(
        request,
        "my_playlists.html",
        {"playlists": playlists, "full_path": full_path, "page_title": _("My playlists")},
    )


@login_required
@csrf_protect
def playlist(request, slug=None):
    if slug:
        playlist = get_object_or_404(Playlist, slug=slug)
        list_videos = playlist.playlistelement_set.all()
    else:
        playlist = None
        list_videos = None
    if (
        playlist
        and request.user != playlist.owner
        and not (
            request.user.is_superuser or request.user.has_perm("playlist.change_playlist")
        )
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this playlist."))
        raise PermissionDenied
    form = PlaylistForm(instance=playlist, initial={"owner": request.user})
    if request.POST and request.POST.get("action"):
        if request.POST["action"] in ACTION:
            return eval("playlist_{0}(request, playlist)".format(request.POST["action"]))
    else:
        return render(
            request, "playlist.html", {"form": form, "list_videos": list_videos}
        )


# @login_required
# @csrf_protect
def playlist_play(request, slug=None):
    template_video = (
        "playlist_player-iframe.html"
        if (request.GET.get("is_iframe"))
        else "playlist_player.html"
    )
    playlist = get_object_or_404(Playlist, slug=slug) if slug is not None else None
    if playlist and request.user != playlist.owner and not playlist.visible:
        # not (request.user.is_superuser or request.user.has_perm(
        #        "video.change_theme")
        messages.add_message(
            request,
            messages.ERROR,
            _("You don't have access to this playlist."),
        )
        raise PermissionDenied
    video = None
    position = (
        int(request.GET.get("p", 1)) - 1
        if request.GET.get("p", "1").isnumeric()
        and int(request.GET.get("p", 1)) > 0
        and int(request.GET.get("p", 1)) <= playlist.playlistelement_set.all().count()
        else 0
    )

    if playlist.playlistelement_set.all().count() > position:
        video = list(playlist.playlistelement_set.all())[position].video
        # video = playlist.playlistelement_set.first().video
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("You don't have access to this playlist."),
        )
        raise PermissionDenied

    listNotes = get_video_adv_note_list(request, video)
    return render(
        request,
        template_video,
        {"playlist": playlist, "video": video, "listNotes": listNotes},
    )


def get_video_adv_note_list(request, video):
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
        AdvancedNotes.objects.filter(video=video)
        .filter(filter)
        .order_by("timestamp", "added_on")
    )


def check_playlist_videos(playlist, data):
    for slug in data:
        element = get_object_or_404(PlaylistElement, video__slug=slug, playlist=playlist)
        if element.video.is_draft:
            return _("A video in draft mode cannot be added to a playlist.")
        if element.video.password:
            return _("A video with a password cannot be added to a playlist.")
    return None


def playlist_move(request, playlist):
    if request.is_ajax():
        if request.POST.get("videos"):
            data = json.loads(request.POST["videos"])
            err = check_playlist_videos(playlist, data)
            if err:
                some_data_to_dump = {"fail": "{0}".format(err)}
            else:
                for slug in data:
                    element = get_object_or_404(
                        PlaylistElement, video__slug=slug, playlist=playlist
                    )
                    element.position = data[slug]
                    element.save()
                some_data_to_dump = {
                    "success": "{0}".format(_("The playlist has been saved!"))
                }
        else:
            some_data_to_dump = {
                "fail": "{0}".format(_("The request is wrong. No video given."))
            }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    return HttpResponseBadRequest(_("Only ajax request are accepted for this action."))


def playlist_remove(request, playlist):
    if request.is_ajax():
        if request.POST.get("video"):
            slug = request.POST["video"]
            element = get_object_or_404(
                PlaylistElement, video__slug=slug, playlist=playlist
            )
            element.delete()
            some_data_to_dump = {
                "success": "{0}".format(
                    _("This video has been removed from your playlist.")
                )
            }
        else:
            some_data_to_dump = {
                "fail": "{0}".format(_("The request is wrong. No video given."))
            }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    return HttpResponseBadRequest(_("Only ajax request are accepted for this action."))


def playlist_edit(request, playlist):
    if playlist:
        list_videos = playlist.playlistelement_set.all()
    else:
        list_videos = None
    form = PlaylistForm(request.POST, instance=playlist)
    if form.is_valid():
        playlist = form.save()
        messages.add_message(request, messages.INFO, _("The playlist have been saved."))
    else:
        messages.add_message(
            request,
            messages.ERROR,
            _("One or more errors have been found in the form."),
        )
    return render(request, "playlist.html", {"form": form, "list_videos": list_videos})


def playlist_add(request, playlist):
    if request.is_ajax():
        if request.POST.get("video"):
            video = get_object_or_404(Video, slug=request.POST["video"])
            msg = None
            if video.is_draft:
                msg = _("A video in draft mode cannot be added to a playlist.")
            if video.password:
                msg = _("A video with a password cannot be added to a playlist.")

            if msg:
                some_data_to_dump = {"fail": "{0}".format(msg)}
            else:
                new = PlaylistElement()
                new.playlist = playlist
                new.video = video
                new.position = playlist.last()
                new.save()
                some_data_to_dump = {
                    "success": "{0}".format(
                        _("The video has been added to your playlist.")
                    )
                }
        else:
            some_data_to_dump = {
                "fail": "{0}".format(_("The request is wrong. No video given."))
            }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    return HttpResponseBadRequest(_("Only ajax request are accepted for this action."))


def playlist_delete(request, playlist):
    if request.is_ajax():
        if playlist:
            playlist.delete()
        some_data_to_dump = {
            "success": "{0}".format(_("This playlist has been deleted."))
        }
        data = json.dumps(some_data_to_dump)
        return HttpResponse(data, content_type="application/json")
    return HttpResponseBadRequest(_("Only ajax request are accepted for this action."))
