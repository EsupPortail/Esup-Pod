from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Building, Broadcaster
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponseNotFound


def lives(request):  # affichage des directs

    site = get_current_site(request)
    buildings = Building.objects.all().filter(sites=site)
    return render(request, "live/lives.html", {
        'buildings': buildings
    })


def video_live(request, id):  # affichage des directs
    broadcaster = get_object_or_404(Broadcaster, id=id)
    if(get_current_site(request) not in broadcaster.sites.all()):
        return HttpResponseNotFound()
    if broadcaster.is_restricted and not request.user.is_authenticated():
        iframe_param = 'is_iframe=true&' if (
            request.GET.get('is_iframe')) else ''
        return redirect(
            '%s?%sreferrer=%s' % (
                settings.LOGIN_URL,
                iframe_param,
                request.get_full_path())
        )
    return render(request, "live/live.html", {
        'broadcaster': broadcaster
    })


""" use rest api to change status
def change_status(request, slug):
    broadcaster = get_object_or_404(Broadcaster, slug=slug)
    if request.GET.get("online") == "1":
        broadcaster.status = 1
    else:
        broadcaster.status = 0
    broadcaster.save()
    return HttpResponse("ok")
"""
