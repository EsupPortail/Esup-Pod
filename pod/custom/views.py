from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from pod.video.models import Video, Channel
from pod.playlist.models import Playlist
# Create your views here.
def homepage(request):
    return render(request, 'custom/pod_home.html', {})


class VideoListView(ListView):
    model= Video
    context_object_name ="videos"
    template_name = "custom/pod_home.html"
    queryset = Video.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs);
        p  = Playlist()
        context['playlists'] = p.get_carousel_playlist()
        context['channels'] = Channel.get_official_channels()
        return context
