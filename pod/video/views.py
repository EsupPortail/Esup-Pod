from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from pod.video.models import Video
from pod.video.models import Channel
from pod.video.models import Theme
from tagging.models import TaggedItem

# Create your views here.
VIDEOS = Video.objects.filter(encoding_in_progress=False, is_draft=False)


def channel(request, slug_c, slug_t=None):
    channel = get_object_or_404(Channel, slug=slug_c)

    videos_list = VIDEOS.filter(channel=channel)

    theme = None
    if slug_t:
        theme = get_object_or_404(Theme, slug=slug_t)
        list_theme = theme.get_all_children_flat()
        videos_list = videos_list.filter(theme__in=list_theme)

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

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html', 
            {'videos': videos, "full_path": full_path})

    return render(request, 'channel/channel.html',
                  {'channel': channel,
                   'videos': videos,
                   'theme': theme,
                   'full_path': full_path})


def get_videos_list(request):
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
    return videos_list


def videos(request):
    videos_list = get_videos_list(request)

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

    if request.is_ajax():
        return render(
            request, 'videos/video_list.html', 
            {'videos': videos, "full_path": full_path})

    return render(request, 'videos/videos.html', {
        'videos': videos,
        "types": request.GET.getlist('type'),
        "owners": request.GET.getlist('owner'),
        "disciplines": request.GET.getlist('discipline'),
        "tags_slug": request.GET.getlist('tag'),
        "full_path": full_path
    })


@csrf_protect
def video(request, slug):
    try:
        id = int(slug[:slug.find("-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)

    return render(request, 'videos/video.html', {
        'video': video}
    )


@csrf_protect
def video_edit(request, slug=None):

    form = "Formulaire de creation/edition d'une video"

    return render(request, 'videos/video_edit.html', {
        'form': form}
    )
