from django.conf.urls import url
from pod.playlist.views import my_playlists
from pod.playlist.views import playlist_play
from pod.playlist.views import playlist

app_name = "playlist"

urlpatterns = [
    url(r"^edit/$", playlist, name="playlist_edit"),
    url(r"^edit/(?P<slug>[\-\d\w]+)/$", playlist, name="playlist_edit"),
    url(r"^my/$", my_playlists, name="my_playlists"),
    url(r"^(?P<slug>[\-\d\w]+)/$", playlist_play, name="playlist"),
]
