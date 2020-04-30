from django.conf import settings as django_settings
from django import template
from django.utils.text import capfirst
from django.urls import reverse
from django.db.models import Q
from django.contrib.sites.shortcuts import get_current_site

from ..forms import VideoVersionForm
from ..models import Video

import importlib

register = template.Library()

HOMEPAGE_SHOWS_PASSWORDED = getattr(
    django_settings,
    'HOMEPAGE_SHOWS_PASSWORDED',
    True)
HOMEPAGE_SHOWS_RESTRICTED = getattr(
    django_settings,
    'HOMEPAGE_SHOWS_RESTRICTED',
    True)


@register.simple_tag
def get_app_link(video, app):
    mod = importlib.import_module('pod.%s.models' % app)
    if hasattr(mod, capfirst(app)):
        video_app = eval(
            'mod.%s.objects.filter(video__id=%s).all()' % (
                capfirst(app), video.id))
        if (app == "interactive"
                and video_app.first() is not None
                and video_app.first().is_interactive() is False):
            video_app = False
        if video_app:
            url = reverse('%(app)s:video_%(app)s' %
                          {"app": app}, kwargs={'slug': video.slug})
            return ('<a href="%(url)s" title="%(app)s" '
                    'class="dropdown-item" target="_blank">%(link)s</a>') % {
                "app": app,
                "url": url,
                "link": mod.__NAME__}
    return ""


@register.simple_tag
def get_version_form(video):
    form = VideoVersionForm()
    return form


@register.simple_tag(takes_context=True)
def get_last_videos(context):
    request = context['request']
    videos = Video.objects.filter(
        encoding_in_progress=False, is_draft=False,
        sites=get_current_site(request)).exclude(
            channel__visible=0)

    if not HOMEPAGE_SHOWS_PASSWORDED:
        videos = videos.filter(
            Q(password='') | Q(password__isnull=True))
    if not HOMEPAGE_SHOWS_RESTRICTED:
        videos = videos.filter(is_restricted=False)
    videos = videos.defer(
        "video", "slug", "owner", "additional_owners", "description")
    count = 0
    recent_vids = []
    for vid in videos:
        if(vid.encoded):
            recent_vids.append(vid)
            count = count + 1
        if(count >= 12):
            break

    return recent_vids
