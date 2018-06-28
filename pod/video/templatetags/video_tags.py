from django import template
from django.utils.text import capfirst
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

import importlib

register = template.Library()


@register.simple_tag
def get_app_link(video, app):
    mod = importlib.import_module('pod.%s.models' % app)
    if hasattr(mod, capfirst(app)):
        video_app = eval(
            'mod.%s.objects.filter(video__id=%s).all()' % (
                capfirst(app), video.id))
        if video_app:
            url = reverse('%(app)s:video_%(app)s' %
                          {"app": app}, kwargs={'slug': video.slug})
            return ('<a href="%(url)s" title="%(app)s" '
                    'class="nav-link">%(link)s</a>') % {
                "app": app,
                "url": url,
                "link": _('%s' % app)}
    return ""
