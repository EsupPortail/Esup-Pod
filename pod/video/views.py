# from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from pod.video.models import Video

# Create your views here.
VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False)

def videos(request):
    videos_list = VIDEOS
    page = request.GET.get('page', 1)
    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)
    return render(request, 'videos/videos.html', {'videos': videos})


@csrf_protect
def video(request, slug):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)

    return HttpResponse("You're looking video %s." % video)
