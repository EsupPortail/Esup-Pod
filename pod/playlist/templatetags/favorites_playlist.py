from django.template import Library

from pod.playlist.utils import get_favorite_playlist_for_user

from ..models import Playlist

register = Library()

@register.simple_tag(name="get_favorite_playlist")
def get_favorite_playlist(user):
    return get_favorite_playlist_for_user(user)
