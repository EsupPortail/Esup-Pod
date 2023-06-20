from django.template import Library

from pod.playlist.utils import get_number_video_added_in_specific_playlist, get_total_favorites_video
from pod.video.models import Video

from ..models import Playlist

register = Library()


@register.simple_tag(takes_context=True, name="get_number_favorites")
def get_number_favorites(context: dict) -> int:
    """Get the number of times a video has been added in favorites."""
    user = context["request"].user
    favorites_playlist = Playlist.objects.get(name="Favorites", owner=user)
    return get_number_video_added_in_specific_playlist(favorites_playlist)

@register.simple_tag(name="get_total_favorites_video")
def get_total_favorites_video(video: Video) -> int:
    """Get the number of times a video has been added in favorites."""
    return get_total_favorites_video(video)

@register.simple_tag(name="get_count_video_added_in_playlist")
def get_count_video_added_in_playlist(video: Video) -> int:
    """Get the number of times a video has been added in a playlist."""
    return get_total_favorites_video(video)
