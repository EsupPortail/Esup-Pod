from __future__ import unicode_literals

from django import template
from django.template.loader import get_template
from django.conf import settings
from pod.video.models import Channel
from django.db.models import Count

register = template.Library()

t = get_template('custom/layouts/partials/_channel_list.html')


def get_official_channels():
    # replace .filter(id__lt=9) by .all()
    return {
            'channels': Channel.objects.all().exclude(
                visible=0).order_by('id').distinct().annotate(
                    video_count=Count("video", distinct=True)
                ), 'DEFAULT_IMG': settings.DEFAULT_IMG
            }


register.inclusion_tag(t)(get_official_channels)
