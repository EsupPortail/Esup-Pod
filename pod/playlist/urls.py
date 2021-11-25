from django.conf.urls import url
from pod.playlist.views import my_playlists
from pod.playlist.views import playlist_play
from pod.playlist.views import playlist

urlpatterns = [
    url(r"^playlist/edit/$", playlist, name="playlist_edit"),
    url(r"^playlist/edit/(?P<slug>[\-\d\w]+)/$", playlist, name="playlist_edit"),
    url(r"^playlist/(?P<slug>[\-\d\w]+)/$", playlist_play, name="playlist"),
    url(r"^my_playlists/$", my_playlists, name="my_playlists"),
]
