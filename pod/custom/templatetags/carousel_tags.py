from django import template
from django.template.loader import get_template
from pod.playlist.models import Playlist

register = template.Library()

t = get_template('custom/layouts/partials/_carousel.html')


def get_carousel_playlist():
    info = Playlist.objects.get(title__startswith="carousel")
    videos = info.videos()
    playlist = {
            'info': info,
            'videos': videos
    }
    return {
        'playlist': playlist,
    }


register.inclusion_tag(t)(get_carousel_playlist)
