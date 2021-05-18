from django.conf.urls import url
from pod.playlist.views import my_playlists
from pod.playlist.views import playlist

urlpatterns = [
    url(r"^playlist/$", playlist, name="playlist"),
    url(r"^playlist/(?P<slug>[\-\d\w]+)/$", playlist, name="playlist"),
    url(r"^my_playlists/$", my_playlists, name="my_playlists"),
]
