from django.shortcuts import render
from django.shortcuts import get_object_or_404
from .models import Building, Broadcaster
from django.conf import settings
from django.shortcuts import redirect


def lives(request):  # affichage des directs
    buildings = Building.objects.all()
    return render(request, "live/lives.html", {
        'buildings': buildings
    })


def video_live(request, id):  # affichage des directs
    broadcaster = get_object_or_404(Broadcaster, id=id)
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
