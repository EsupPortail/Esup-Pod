from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from pod.video.models import Video
# Create your views here.
def homepage(request):
    return render(request, 'custom/pod_home.html', {})


class VideoListView(ListView):
    model= Video
    context_object_name ="videos"
    template_name = "custom/pod_home.html"
    queryset = Video.objects.all()
    
