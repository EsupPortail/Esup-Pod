from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required(redirect_field_name="referrer")
def playlist_list(request):
    """Render my playlists page."""
    return render(
        request,
        "playlist/playlists.html",
    )
