# from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from pod.video.models import Video

from string import find

# Create your views here.


@csrf_protect
def video(request, slug):
    try:
        id = int(slug[:find(slug, "-")])
    except ValueError:
        raise SuspiciousOperation('Invalid video id')
    video = get_object_or_404(Video, id=id)

    return HttpResponse("You're looking video %s." % video)
