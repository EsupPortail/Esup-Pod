from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count, Sum, Q
from django.db.models import Prefetch
from django.db.models.functions import Substr, Lower
from datetime import timedelta

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
USE_PODFILE = getattr(django_settings, 'USE_PODFILE', False)
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
        'LOGO_SITE': 'img/logoPod.svg',
        'LOGO_ETB': 'img/logo_etb.svg',
        'LOGO_PLAYER': 'img/logoPod.svg',
        'LINK_PLAYER': '',
        'FOOTER_TEXT': ('',),
        'FAVICON': 'img/logoPod.svg',
        'CSS_OVERRIDE': '',
        'PRE_HEADER_TEMPLATE': '',
        'POST_FOOTER_TEMPLATE': '',
        'TRACKING_TEMPLATE': '',
    }
)
OEMBED = getattr(
    django_settings, 'OEMBED', False)

HIDE_USERNAME = getattr(
        django_settings, 'HIDE_USERNAME', False)

HIDE_USER_TAB = getattr(
        django_settings, 'HIDE_USER_TAB', False)

HIDE_USER_FILTER = getattr(
        django_settings, 'HIDE_USER_FILTER', False)

USE_STATS_VIEW = getattr(
        django_settings, 'USE_STATS_VIEW', False)

ALLOW_MANUAL_RECORDING_CLAIMING = getattr(
        django_settings, 'ALLOW_MANUAL_RECORDING_CLAIMING', False)
SHIB_URL = getattr(
        django_settings, 'SHIB_URL', "/idp/shibboleth.sso/Login")
USE_SHIB = getattr(
        django_settings, 'USE_SHIB', False)

USE_RECORD_PREVIEW = getattr(
        django_settings, 'USE_RECORD_PREVIEW', False)
SHIB_NAME = getattr(
        django_settings, 'SHIB_NAME', "Identify Federation")


def context_settings(request):
    new_settings = {}
    for sett in TEMPLATE_VISIBLE_SETTINGS:
        try:
            new_settings[sett] = TEMPLATE_VISIBLE_SETTINGS[sett]
        except AttributeError:
            m = "TEMPLATE_VISIBLE_SETTINGS: '{0}' does not exist".format(sett)
            raise ImproperlyConfigured(m)
    new_settings['VERSION'] = VERSION
    new_settings['USE_PODFILE'] = USE_PODFILE
    new_settings["THIRD_PARTY_APPS"] = django_settings.THIRD_PARTY_APPS
    new_settings['OEMBED'] = OEMBED
    new_settings['HIDE_USERNAME'] = HIDE_USERNAME
    new_settings['HIDE_USER_TAB'] = HIDE_USER_TAB
    new_settings['HIDE_USER_FILTER'] = HIDE_USER_FILTER
    new_settings['USE_STATS_VIEW'] = USE_STATS_VIEW
    new_settings['USE_RECORD_PREVIEW'] = USE_RECORD_PREVIEW
    new_settings['SHIB_NAME'] = SHIB_NAME
    new_settings['ALLOW_MANUAL_RECORDING_CLAIMING'] = \
        ALLOW_MANUAL_RECORDING_CLAIMING
    new_settings['SHIB_URL'] = \
        SHIB_URL
    new_settings['USE_SHIB'] = \
        USE_SHIB
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
    VALUES_LIST.append('fl_firstname')

    owners = Owner.objects.filter(**owners_filter_args).distinct().order_by(
        ORDER_BY).annotate(video_count=Count(
            "video", distinct=True)).annotate(
        fl_name=Lower(Substr("last_name", 1, 1))).annotate(
        fl_firstname=Lower(Substr("first_name", 1, 1))).order_by(
        'fl_name').values(*list(VALUES_LIST))

    if not request.user.is_authenticated:
        listowner = {}
    else:
        listowner = get_list_owner(owners)

    LAST_VIDEOS = get_last_videos() if request.path == "/" else None

    list_videos = Video.objects.filter(
        encoding_in_progress=False,
        is_draft=False)
    VIDEOS_COUNT = list_videos.count()
    VIDEOS_DURATION = str(timedelta(
        seconds=list_videos.aggregate(Sum('duration'))['duration__sum']
    )) if list_videos.aggregate(Sum('duration'))['duration__sum'] else 0

    return {'ALL_CHANNELS': all_channels, 'CHANNELS': channels,
            'TYPES': types, 'OWNERS': owners,
            'DISCIPLINES': disciplines, 'LISTOWNER': json.dumps(listowner),
            'LAST_VIDEOS': LAST_VIDEOS, 'LINK_FOOTER': linkFooter,
            'VIDEOS_COUNT': VIDEOS_COUNT,
            'VIDEOS_DURATION': VIDEOS_DURATION
            }


def get_list_owner(owners):
    listowner = {}
    for owner in owners:
        if owner['fl_name'] != '':
            if listowner.get(owner['fl_name']):
                listowner[owner['fl_name']].append(owner)
            else:
                listowner[owner['fl_name']] = [owner]
        if (owner['fl_firstname'] != ''
                and owner['fl_firstname'] != owner['fl_name']):
            if listowner.get(owner['fl_firstname']):
                listowner[owner['fl_firstname']].append(owner)
            else:
                listowner[owner['fl_firstname']] = [owner]
    return listowner


def get_last_videos():

    filter_args = Video.objects.filter(
        encoding_in_progress=False, is_draft=False)

    if not HOMEPAGE_SHOWS_PASSWORDED:
        filter_args = filter_args.filter(
            Q(password='') | Q(password__isnull=True))
    if not HOMEPAGE_SHOWS_RESTRICTED:
        filter_args = filter_args.filter(is_restricted=False)

    return filter_args.exclude(channel__visible=0)[:12]
