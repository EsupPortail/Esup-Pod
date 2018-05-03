# from django.shortcuts import render
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from pod.video.models import Video
from tagging.models import TaggedItem

# Create your views here.
VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False)


def videos(request):
    videos_list = VIDEOS

    if request.GET.getlist('type'):
        videos_list = videos_list.filter(
            type__slug__in=request.GET.getlist('type'))
    if request.GET.getlist('discipline'):
        videos_list = videos_list.filter(
            discipline__slug__in=request.GET.getlist('discipline'))
    if request.GET.getlist('owner'):
        videos_list = videos_list.filter(
            owner__username__in=request.GET.getlist('owner'))
    if request.GET.getlist('tag'):
        videos_list = TaggedItem.objects.get_union_by_model(
            videos_list,
            request.GET.getlist('tag'))

    page = request.GET.get('page', 1)
    full_path = ""
    if page:
        full_path = request.get_full_path().replace(
            "?page=%s" % page, "").replace("&page=%s" % page, "")
    paginator = Paginator(videos_list, 12)
    try:
        videos = paginator.page(page)
    except PageNotAnInteger:
        videos = paginator.page(1)
    except EmptyPage:
        videos = paginator.page(paginator.num_pages)
    return render(request, 'videos/videos.html', {
        'videos': videos,
        "types": request.GET.getlist('type'),
        "owners": request.GET.getlist('owner'),
        "disciplines": request.GET.getlist('discipline'),
        "tags_slug": request.GET.getlist('tag'),
        "full_path":full_path
    })


@csrf_protect
def video(request, slug):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)

    return HttpResponse("You're looking video %s." % video)
