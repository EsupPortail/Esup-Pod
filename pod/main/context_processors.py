from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from django.db.models import Prefetch
from django.db.models.functions import Substr, Lower

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline

import json

from django.contrib.auth.models import User as Owner
ORDER_BY = 'last_name'
VALUES_LIST = ['username', 'first_name', 'last_name']

MENUBAR_HIDE_INACTIVE_OWNERS = getattr(
    django_settings, 'MENUBAR_HIDE_INACTIVE_OWNERS', False)
MENUBAR_SHOW_STAFF_OWNERS_ONLY = getattr(
    django_settings, 'MENUBAR_SHOW_STAFF_OWNERS_ONLY', False)


def context_settings(request):
    new_settings = {}
    for attr in getattr(django_settings, 'TEMPLATE_VISIBLE_SETTINGS', []):
        try:
            new_settings[attr] = getattr(django_settings, attr)
        except AttributeError:
            m = "TEMPLATE_VISIBLE_SETTINGS: '{0}' does not exist".format(attr)
            raise ImproperlyConfigured(m)
    return new_settings


def context_navbar(request):
    channels = Channel.objects.filter(
        visible=True, video__is_draft=False
    ).distinct().annotate(
        video_count=Count("video", distinct=True)
    ).prefetch_related(
        Prefetch("themes", queryset=Theme.objects.filter(
            parentId=None
        ).distinct().annotate(
            video_count=Count("video", distinct=True)
        )))
    types = Type.objects.filter(
        video__is_draft=False
    ).distinct().annotate(video_count=Count("video", distinct=True))

    disciplines = Discipline.objects.filter(
        video__is_draft=False
    ).distinct().annotate(video_count=Count("video", distinct=True))

    owners_filter_args = {}
    if MENUBAR_HIDE_INACTIVE_OWNERS:
        owners_filter_args['is_active'] = True
    if MENUBAR_SHOW_STAFF_OWNERS_ONLY:
        owners_filter_args['is_staff'] = True

    VALUES_LIST.append('video_count')
    VALUES_LIST.append('fl_name')

    owners = Owner.objects.filter(**owners_filter_args).order_by(
        ORDER_BY).annotate(video_count=Count(
            "video", distinct=True)).annotate(
        fl_name=Lower(Substr(ORDER_BY, 1, 1))).order_by(
        'fl_name').values(*list(VALUES_LIST))

    listowner = {}
    for owner in owners:
        if owner['fl_name'] != '':
            if listowner.get(owner['fl_name']):
                listowner[owner['fl_name']].append(owner)
            else:
                listowner[owner['fl_name']] = [owner]

    return {'CHANNELS': channels, 'TYPES': types, 'OWNERS': owners,
            'DISCIPLINES':disciplines, 'LISTOWNER': json.dumps(listowner)}
