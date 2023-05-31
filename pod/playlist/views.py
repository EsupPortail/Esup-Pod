from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from pod import playlist
from pod.playlist.models import Playlist
from django.utils.translation import ugettext_lazy as _

from pod.playlist.utils import get_playlist, get_video_list_for_playlist
from pod.main.utils import is_ajax

from pod.video.views import CURSUS_CODES, get_owners_has_instances


from .models import Playlist

@login_required(redirect_field_name="referrer")
def playlist_list(request):
    """Render my playlists page."""
    return render(
        request,
        "playlist/playlists.html",
        {
            "page_title": _("Playlists"),
            "playlists": ['lol', 'lol2'],
        }
    )


@login_required(redirect_field_name="referrer")
def playlist_content(request, slug):
    """Render the videos list of a playlist."""
    sort_field = request.GET.get("sort", "rank")
    sort_direction = request.GET.get("sort_direction")
    playlist = get_playlist(slug)
    videos_list = get_video_list_for_playlist(playlist)

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
            "playlist/playlist.html",
            {"videos": videos, "full_path": full_path, "count_videos": count_videos},
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
