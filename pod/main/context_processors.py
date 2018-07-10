from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from django.db.models import Prefetch
from django.db.models.functions import Substr, Lower

from pod.main.models import LinkFooter

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.models import Video

import json

from django.contrib.auth.models import User as Owner
ORDER_BY = 'last_name'
VALUES_LIST = ['username', 'first_name', 'last_name']

MENUBAR_HIDE_INACTIVE_OWNERS = getattr(
    django_settings, 'MENUBAR_HIDE_INACTIVE_OWNERS', False)
MENUBAR_SHOW_STAFF_OWNERS_ONLY = getattr(
    django_settings, 'MENUBAR_SHOW_STAFF_OWNERS_ONLY', False)
HOMEPAGE_SHOWS_PASSWORDED = getattr(
    django_settings,
    'HOMEPAGE_SHOWS_PASSWORDED',
    True)
HOMEPAGE_SHOWS_RESTRICTED = getattr(
    django_settings,
    'HOMEPAGE_SHOWS_RESTRICTED',
    True)

VERSION = getattr(
    django_settings,
    'VERSION',
    '2.X')
##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    django_settings,
    'TEMPLATE_VISIBLE_SETTINGS',
    {
        'TITLE_SITE': 'Pod',
        'TITLE_ETB': 'University name',
        'LOGO_SITE': 'img/logo_compact.png',
        'LOGO_COMPACT_SITE': 'img/logo_compact_site.png',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logo_player.png',
        'FOOTER_TEXT': ('',),
        # 'FAVICON': 'img/favicon.png',
        # 'CSS_OVERRIDE' : 'custom/etab.css'
        # 'LINK_PLAYER':''
    }
)


def context_settings(request):
    new_settings = {}
    for sett in TEMPLATE_VISIBLE_SETTINGS:
        try:
            new_settings[sett] = TEMPLATE_VISIBLE_SETTINGS[sett]
        except AttributeError:
            m = "TEMPLATE_VISIBLE_SETTINGS: '{0}' does not exist".format(sett)
            raise ImproperlyConfigured(m)
    new_settings['VERSION'] = VERSION
    new_settings["THIRD_PARTY_APPS"] = django_settings.THIRD_PARTY_APPS
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

    all_channels = Channel.objects.all(
    ).distinct().annotate(
        video_count=Count("video", distinct=True)
    ).prefetch_related(
        Prefetch("themes", queryset=Theme.objects.all(
        ).distinct().annotate(
            video_count=Count("video", distinct=True)
        )))

    types = Type.objects.filter(
        video__is_draft=False
    ).distinct().annotate(video_count=Count("video", distinct=True))

    disciplines = Discipline.objects.filter(
        video__is_draft=False
    ).distinct().annotate(video_count=Count("video", distinct=True))

    linkFooter = LinkFooter.objects.all()

    owners_filter_args = {
        'video__is_draft': False,
    }
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

    LAST_VIDEOS = get_last_videos() if request.path == "/" else None

    return {'ALL_CHANNELS':all_channels, 'CHANNELS': channels, 'TYPES': types, 
            'OWNERS': owners,
            'DISCIPLINES': disciplines, 'LISTOWNER': json.dumps(listowner),
            'LAST_VIDEOS': LAST_VIDEOS, 'LINK_FOOTER': linkFooter
            }


def get_last_videos():
    filter_args = {"encoding_in_progress": False, "is_draft": False}
    if not HOMEPAGE_SHOWS_PASSWORDED:
        filter_args['password'] = ""
    if not HOMEPAGE_SHOWS_RESTRICTED:
        filter_args['is_restricted'] = False
    return Video.objects.filter(
        **filter_args).exclude(channel__visible=0)[:12]
