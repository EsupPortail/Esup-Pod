from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count, Sum
from django.db.models import Prefetch
from datetime import timedelta

from pod.main.models import LinkFooter

from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Type
from pod.video.models import Discipline
from pod.video.models import Video
from django.contrib.sites.shortcuts import get_current_site

ORDER_BY = 'last_name'
VALUES_LIST = ['username', 'first_name', 'last_name']

MENUBAR_HIDE_INACTIVE_OWNERS = getattr(
    django_settings, 'MENUBAR_HIDE_INACTIVE_OWNERS', False)
MENUBAR_SHOW_STAFF_OWNERS_ONLY = getattr(
    django_settings, 'MENUBAR_SHOW_STAFF_OWNERS_ONLY', False)

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

HIDE_CHANNEL_TAB = getattr(
    django_settings, 'HIDE_CHANNEL_TAB', False)

HIDE_TYPES_TAB = getattr(
    django_settings, 'HIDE_TYPES_TAB', False)

HIDE_LANGUAGE_SELECTOR = getattr(
    django_settings, 'HIDE_LANGUAGE_SELECTOR', False)

HIDE_USER_FILTER = getattr(
    django_settings, 'HIDE_USER_FILTER', False)

USE_STATS_VIEW = getattr(
    django_settings, 'USE_STATS_VIEW', False)

HIDE_TAGS = getattr(
    django_settings, 'HIDE_TAGS', False)

HIDE_SHARE = getattr(
    django_settings, 'HIDE_SHARE', False)

HIDE_DISCIPLINES = getattr(
    django_settings, 'HIDE_DISCIPLINES', False)

ALLOW_MANUAL_RECORDING_CLAIMING = getattr(
    django_settings, 'ALLOW_MANUAL_RECORDING_CLAIMING', False)

USE_RECORD_PREVIEW = getattr(
    django_settings, 'USE_RECORD_PREVIEW', False)
SHIB_NAME = getattr(
    django_settings, 'SHIB_NAME', "Identify Federation")

USE_THEME = getattr(
    django_settings, 'USE_THEME', "default")

BOOTSTRAP_CUSTOM = getattr(
    django_settings, 'BOOTSTRAP_CUSTOM', None)

USE_CHUNKED_UPLOAD = getattr(
    django_settings, 'USE_CHUNKED_UPLOAD', None)

CHUNK_SIZE = getattr(
    django_settings, 'CHUNK_SIZE', 100000)


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
    new_settings['HIDE_CHANNEL_TAB'] = HIDE_CHANNEL_TAB
    new_settings['HIDE_TYPES_TAB'] = HIDE_TYPES_TAB
    new_settings['HIDE_LANGUAGE_SELECTOR'] = HIDE_LANGUAGE_SELECTOR
    new_settings['HIDE_TAGS'] = HIDE_TAGS
    new_settings['HIDE_SHARE'] = HIDE_SHARE
    new_settings['HIDE_DISCIPLINES'] = HIDE_DISCIPLINES
    new_settings['HIDE_USER_FILTER'] = HIDE_USER_FILTER
    new_settings['USE_STATS_VIEW'] = USE_STATS_VIEW
    new_settings['USE_RECORD_PREVIEW'] = USE_RECORD_PREVIEW
    new_settings['SHIB_NAME'] = SHIB_NAME
    new_settings['ALLOW_MANUAL_RECORDING_CLAIMING'] = \
        ALLOW_MANUAL_RECORDING_CLAIMING
    new_settings['USE_THEME'] = USE_THEME
    new_settings['BOOTSTRAP_CUSTOM'] = BOOTSTRAP_CUSTOM
    new_settings['USE_CHUNKED_UPLOAD'] = USE_CHUNKED_UPLOAD
    new_settings['CHUNK_SIZE'] = CHUNK_SIZE
    return new_settings


def context_navbar(request):
    channels = Channel.objects.filter(
        visible=True, video__is_draft=False,
        sites=get_current_site(request)
    ).distinct().annotate(
        video_count=Count("video", distinct=True)
    ).prefetch_related(
        Prefetch("themes", queryset=Theme.objects.filter(
            parentId=None,
            channel__sites=get_current_site(request)
        ).distinct().annotate(
            video_count=Count("video", distinct=True)
        )))

    all_channels = Channel.objects.all(
    ).filter(sites=get_current_site(request)).distinct().annotate(
        video_count=Count("video", distinct=True)
    ).prefetch_related(
        Prefetch("themes", queryset=Theme.objects.filter(
            channel__sites=get_current_site(request)).distinct().annotate(
            video_count=Count("video", distinct=True)
        )))

    types = Type.objects.filter(
        sites=get_current_site(request),
        video__is_draft=False,
    ).distinct().annotate(video_count=Count("video", distinct=True))

    disciplines = Discipline.objects.filter(
        video__is_draft=False, sites=get_current_site(request)
    ).distinct().annotate(video_count=Count("video", distinct=True))

    linkFooter = LinkFooter.objects.all().filter(
        page__sites=get_current_site(request))

    list_videos = Video.objects.filter(
        encoding_in_progress=False,
        is_draft=False, sites=get_current_site(request))
    VIDEOS_COUNT = list_videos.count()
    VIDEOS_DURATION = str(timedelta(
        seconds=list_videos.aggregate(Sum('duration'))['duration__sum']
    )) if list_videos.aggregate(Sum('duration'))['duration__sum'] else 0

    return {'ALL_CHANNELS': all_channels, 'CHANNELS': channels,
            'TYPES': types,
            'DISCIPLINES': disciplines,
            'LINK_FOOTER': linkFooter,
            'VIDEOS_COUNT': VIDEOS_COUNT,
            'VIDEOS_DURATION': VIDEOS_DURATION
            }
