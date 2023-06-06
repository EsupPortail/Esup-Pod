from django.template import Library

from pod.playlist.utils import get_number_video_added_in_specific_playlist

from ..models import Playlist

register = Library()


@register.simple_tag(takes_context=True, name="get_number_favorites")
def get_number_favorites(context: dict) -> int:
    """Get the number of times a video has been added in favorites."""
    user = context["request"].user
    favorites_playlist = Playlist.objects.get(name="Favorites", owner=user)
    return get_number_video_added_in_specific_playlist(favorites_playlist)
