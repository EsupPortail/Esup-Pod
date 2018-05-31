from django.conf.urls import url
from pod.playlist.views import my_playlists

urlpatterns = [
    url(r'^my_playlists/$', my_playlists, name='my_playlists'),
]