from django.template import Library
from pod.playlist.models import Playlist

from pod.playlist.utils import check_video_in_playlist, get_playlist_list_for_user
from pod.video.models import Video

register = Library()


@register.simple_tag(name="get_user_playlists")
def get_user_playlists(user):
    return get_playlist_list_for_user(user)

@register.simple_tag(name="video_in_playlist")
def video_in_playlist(playlist: Playlist, video: Video):
    return check_video_in_playlist(playlist, video)

