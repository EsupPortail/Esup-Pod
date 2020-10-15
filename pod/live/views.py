from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Building, Broadcaster, HeartBeat
from .forms import LivePasswordForm
from django.conf import settings
from django.shortcuts import redirect
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.db.models import Prefetch
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
import json
from django.utils import timezone


def lives(request):  # affichage des directs
    site = get_current_site(request)
    buildings = Building.objects.all().filter(sites=site).prefetch_related(
        Prefetch("broadcaster_set", queryset=Broadcaster.objects.filter(
            public=True)))
    return render(request, "live/lives.html", {
        'buildings': buildings
    })


def get_broadcaster_by_slug(slug, site):
    broadcaster = None
    if slug.isnumeric():
        try:
            broadcaster = Broadcaster.objects.get(
                id=slug, building__sites=site)
        except ObjectDoesNotExist:
            pass
    if broadcaster is None:
        broadcaster = get_object_or_404(Broadcaster, slug=slug,
                                        building__sites=site)
    return broadcaster


def video_live(request, slug):  # affichage des directs
    site = get_current_site(request)
    broadcaster = get_broadcaster_by_slug(slug, site)
    if broadcaster.is_restricted and not request.user.is_authenticated():
        iframe_param = 'is_iframe=true&' if (
            request.GET.get('is_iframe')) else ''
        return redirect(
            '%s?%sreferrer=%s' % (
                settings.LOGIN_URL,
                iframe_param,
                request.get_full_path())
        )
    is_password_protected = (
        broadcaster.password is not None and broadcaster.password != '')
    if is_password_protected and not (request.POST.get('password')
                                      and request.POST.get(
                                          'password') == broadcaster.password):
        form = LivePasswordForm(
            request.POST) if request.POST else LivePasswordForm()
        if (request.POST.get('password')
                and request.POST.get('password') != broadcaster.password):
            messages.add_message(
                request, messages.ERROR,
                _('The password is incorrect.'))
        return render(
            request, 'live/live.html', {
                'broadcaster': broadcaster,
                'form': form,
            }
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


def heartbeat(request):
    if request.is_ajax():
        key = request.GET.get('key', '')
        broadcaster_id = int(request.GET.get('liveid', 0))
        heartbeat = HeartBeat.objects.filter(viewkey=key)
        if heartbeat.count() == 0:
            if request.user.is_anonymous:
                HeartBeat.objects.create(
                    viewkey=key, broadcaster_id=broadcaster_id)
            else:
                HeartBeat.objects.create(
                    viewkey=key, broadcaster_id=1, user=request.user)
        else:
            heartbeat = heartbeat.first()
            heartbeat.last_heartbeat = timezone.now()
            heartbeat.save()
    else:
        return HttpResponseBadRequest()
    mimetype = 'application/json'
    broadcast = Broadcaster.objects.get(id=broadcaster_id)
    viewers = broadcast.viewers.all().values(*list(
        ['first_name', 'last_name', 'is_superuser']))
    return HttpResponse(json.dumps(
        {"viewers": broadcast.viewcount, "viewers_list": list(
            viewers)}), mimetype)
