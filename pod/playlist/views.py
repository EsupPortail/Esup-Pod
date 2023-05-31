from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render

from .utils import get_playlist_list_for_user

@login_required(redirect_field_name="referrer")
def playlist_list(request):
    """Render my playlists page."""
    playlists = get_playlist_list_for_user(request.user)
    return render(
        request,
        "playlist/playlists.html",
        {
            "page_title": _("Playlists"),
            "playlists": playlists,
        }
    )
