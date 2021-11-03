from django.conf.urls import url
from pod.playlist.views import my_playlists
from pod.playlist.views import edit_playlist
from pod.playlist.views import playlist

# urlpatterns = [
#     url(r"^playlist/$", playlist, name="playlist"),
#     url(r"^playlist/(?P<slug>[\-\d\w]+)/$", playlist, name="playlist"),
#     url(r"^my_playlists/$", my_playlists, name="my_playlists"),
# ]
urlpatterns = [
    url(r"^playlist/$", edit_playlist, name="playlist"),
    url(r"^playlist/edit/(?P<slug>[\-\d\w]+)/$", edit_playlist, name="edit_playlist"),
    url(r"^playlist/(?P<slug>[\-\d\w]+)/$", playlist, name="playlist"),
    url(r"^my_playlists/$", my_playlists, name="my_playlists"),
]
