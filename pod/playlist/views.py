from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render

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
