from __future__ import unicode_literals

from django import template
from django.template.loader import get_template
from django.template.context import Context
from django.utils.html import escapejs, format_html
from django.utils.safestring import mark_safe
from django.utils.http import urlencode
from django.core.urlresolvers import reverse
from django.conf import settings
import random
import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count, Case, When, IntegerField, Prefetch
from pod.playlist.models import Playlist
from pod.video.models import Channel, PlaylistVideo, Video


register = template.Library()

t = get_template('custom/layouts/partials/_channel_list.html')

def get_official_channels():
    # replace .filter(id__lt=9) by .all()
    return {
        'channels': Channel.objects.all().exclude(
            visible=0).order_by('id').distinct().annotate(video_count=Count("video", distinct=True)),
        'DEFAULT_IMG': settings.DEFAULT_IMG
    }
register.inclusion_tag(t)(get_official_channels)
