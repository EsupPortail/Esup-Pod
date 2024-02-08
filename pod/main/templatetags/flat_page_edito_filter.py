"""Esup-Pod video custom filters."""
import hashlib
import html
import random
import string
from datetime import date, datetime
from html.parser import HTMLParser

from django import template
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.db.models import Q, Sum
from django.template import loader
from django.utils import timezone

from pod.live.models import Event
from pod.video.models import Video
from pod.playlist.models import PlaylistContent

register = template.Library()
parser = HTMLParser()
html_parser = html

__DEFAULT_NB_ELEMENT__ = 5
__DEFAULT_NB_CARD__ = 5
__DEFAULT_TITLE__ = ""

VIDEO_RECENT_VIEWCOUNT = getattr(settings, "VIDEO_RECENT_VIEWCOUNT", 180)
EDITO_CACHE_TIMEOUT = getattr(settings, "EDITO_CACHE_TIMEOUT", 300)
EDITO_CACHE_PREFIX = getattr(settings, "EDITO_CACHE_PREFIX", "edito_cache_")


@register.filter(name="edito")
def edito(content, request):
    bloc = displayContentByBloc(content, request)
    return bloc


def displayContentByBloc(content, request):
    debugElts = []

    current_site = get_current_site(request)

    md5_part = hashlib.md5(str(content).encode('utf-8')).hexdigest()

    params = dict()

    if (content.debug is True):
        params['debug'] = True
    if (content.debug is False):
        params['debug'] = False

    if ('debug' in request.GET):
        if (request.GET['debug'] is True):
            params['debug'] = True

    if (content.no_cache is True):
        params['cache'] = False
        debugElts.append('Cache is disable for this part')
    if (content.no_cache is False):
        params['cache'] = True
        debugElts.append('Cache is enable for this part')

    if (content.nb_element is not None or content.nb_element != ""):
        params['nb-element'] = int(content.nb_element)
    else:
        params['nb-element'] = __DEFAULT_NB_ELEMENT__

    if (content.slider_multi_nb is not None or content.slider_multi_nb != ""):
        params['slider-multi-nb-card'] = int(content.slider_multi_nb)
    else:
        params['slider-multi-nb-card'] = __DEFAULT_NB_CARD__

    if (content.display_title is not None):
        params['title'] = content.display_title
    else:
        params['title'] = __DEFAULT_TITLE__

    if (content.show_restricted is True):
        params['show-restricted'] = True
    if (content.show_restricted is False):
        params['show-restricted'] = False

    if (content.view_videos_from_non_visible_channels is True):
        params['view-videos-from-non-visible-channels'] = True
    if (content.view_videos_from_non_visible_channels is False):
        params['view-videos-from-non-visible-channels'] = False

    if (content.shows_passworded is True):
        params['show-passworded'] = True
    if (content.shows_passworded is False):
        params['show-passworded'] = False

    if (content.must_be_auth is True):
        params['mustbe-auth'] = True
    if (content.must_be_auth is False):
        params['mustbe-auth'] = False

    if (content.auto_slide is True):
        params['auto-slide'] = True
    if (content.auto_slide is False):
        params['auto-slide'] = False

    if (content.data_type == 'channel'):
        params['fct'] = 'render_base_videos'
        params['container'] = 'channel'
        params['data'] = content.Channel

    if (content.data_type == 'theme'):
        params['fct'] = 'render_base_videos'
        params['container'] = 'theme'
        params['data'] = content.Theme

    if (content.data_type == 'playlist'):
        params['fct'] = 'render_base_videos'
        params['container'] = 'playlist'
        params['data'] = content.Playlist

    if (content.data_type == 'event_next'):
        params['fct'] = 'render_next_events'

    if (content.data_type == 'most_views'):
        params['fct'] = 'render_most_view'

    if (content.data_type == 'last_videos'):
        params['fct'] = 'render_last_view'

    if (content.type == 'html'):
        params['template'] = 'bloc/html.html'
        params['fct'] = 'render_html'
        params['data'] = content.html

    if (content.type == 'slider'):
        params['template'] = 'bloc/slider.html'
    if (content.type == 'slider_multi'):
        params['template'] = 'bloc/slider_multi.html'
    if (content.type == 'card_list'):
        params['template'] = 'bloc/card_list.html'

    cached_content_part = None

    if params['mustbe-auth'] and not request.user.is_authenticated:
        debugElts.append('User is not authenticated and mustbe-auth=true hide result')
        content_part = ''
    else:
        if params['cache']:
            cached_content_part = cache.get(EDITO_CACHE_PREFIX + md5_part)

        if cached_content_part:
            debugElts.append('Found in cache')
            content_part = cached_content_part
        else:
            debugElts.append('Not found in cache')
            uniq_id = ''.join(random.choice(string.ascii_letters) for i in range(20))
            content_part = globals()["%s" % params['fct']](uniq_id, params, current_site, debugElts)
            cache.set(EDITO_CACHE_PREFIX + md5_part, content_part, timeout=EDITO_CACHE_TIMEOUT)

    if params['debug']:
        content_part = "<pre>%s</pre>%s" % ('\n'.join(debugElts), content_part)

    content = content_part

    return (content)


def render_base_videos(uniq_id, params, current_site, debugElts):
    debugElts.append('Call function render_base_videos')

    container = params['data']

    filters = {}

    if (params['container'] == 'playlist'):
        container_playlist = PlaylistContent.objects.filter(
            playlist=params['data']
        )
        container_playlistContent = []
        for list in container_playlist:
            container_playlistContent.append(list.video.id)
        filters["id__in"] = container_playlistContent
    else:
        if (params['container'] == "theme"):
            container_childrens = container.get_all_children_flat()
            filters["theme__in"] = container_childrens
            if (params['debug']):
                if (len(container_childrens) > 1):
                    debugElts.append('Theme has children(s)')
                    for children in container_childrens:
                        debugElts.append(' - children found [ID:%s] [SLUG:%s] [TITLE:%s]' % (children.id, children.slug, children.title))
        else:
            filters[params['container']] = container

    filters['encoding_in_progress'] = False
    filters['is_draft'] = False
    filters['sites'] = current_site

    filter_q = Q(**filters)

    query = Video.objects.filter(
        filter_q)

    query = addfilter(params, debugElts, query)

    videos = query.all().defer("video", "slug", "description").distinct()[:params['nb-element']]

    if params['debug']:
        debugElts.append(f"Database query '{str(videos.query)}'")
        debugElts.append('Found videos in container :')
        for video in videos:
            debugElts.append(f' - Video informations : [ID:{video.id}] [SLUG:{video.slug}] [TITLE:{video.title}]')

    if (params['title'] == ''):
        if (params['container'] == 'playlist'):
            title = container.name
        else:
            title = container.title
    else:
        title = params['title']

    if videos.count() < params['slider-multi-nb-card']:
        params['slider-multi-nb-card'] = videos.count()

    part_content = loader.get_template(params['template']).render(
        {
            "uniq_id": uniq_id,
            "container": container,
            "title" : title,
            "type": 'video',
            "elements" : videos,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']
        }
    )
    return part_content


def render_most_view(uniq_id, params, current_site, debugElts):
    debugElts.append('Call function render_most_view')

    d = date.today() - timezone.timedelta(days=VIDEO_RECENT_VIEWCOUNT)
    query = Video.objects.filter(
        Q(encoding_in_progress=False)
        & Q(is_draft=False)
        & Q(viewcount__date__gte=d)
        & Q(sites=current_site)
    ).annotate(nombre=Sum('viewcount'))

    query = addfilter(params, debugElts, query)

    most_viewed_videos = query.all().order_by('-nombre')[:int(params['nb-element'])]

    debugElts.append(f"Database query '{str(most_viewed_videos.query)}'")

    debugElts.append('Found videos in container :')

    for video in most_viewed_videos:
        debugElts.append(f' - Video informations : '
                         f'[ID:{video.id}] [SLUG:{video.slug}] [RECENT_VIW_COUNT:{video.recentViewcount}]')

    if most_viewed_videos.count() < params['slider-multi-nb-card']:
        params['slider-multi-nb-card'] = most_viewed_videos.count()

    if (params['title'] == ''):
        title = 'Les plus vues'
    else:
        title = params['title']

    part_content = loader.get_template(params['template']).render(
        {
            "uniq_id": uniq_id,
            "title" : title,
            "type": 'video',
            "elements" : most_viewed_videos,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']
        }
    )
    return "%s" % (part_content)


def render_next_events(uniq_id, params, current_site, debugElts):
    debugElts.append('Call function render_next_events')

    query = Event.objects\
        .filter(is_draft=False)\
        .exclude(end_date__lt=datetime.now())\
        .filter(broadcaster__building__sites__exact=current_site)

    if not params['show-restricted']:
        query = query.filter(is_restricted=False)

    event_list = query.all().order_by("start_date")[:params['nb-element']]

    if params['debug']:
        debugElts.append(f"Database query '{event_list.query}'")
        debugElts.append('Found events in container :')
        for event in event_list:
            debugElts.append(f" - Video informations is [ID:{event.id}] [SLUG:{event.slug}] [TITLE:{event.title}]")

    if event_list.count() < params['slider-multi-nb-card']:
        params['slider-multi-nb-card'] = event_list.count()

    if (params['title'] == ''):
        title = 'Les prochains événements'
    else:
        title = params['title']

    part_content = loader.get_template(params['template']).render(
        {
            "uniq_id": uniq_id,
            "title": title,
            "type": 'event',
            "elements": event_list,
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card": params['slider-multi-nb-card']
        }
    )
    return part_content


def render_html(uniq_id, params, current_site, debugElts):
    debugElts.append('Call function render_html')

    part_content = loader.get_template(params['template']).render(
        {
            "body": params['data']
        }
    )
    return "%s" % (part_content)


def render_last_view(uniq_id, params, current_site, debugElts):
    debugElts.append('Call function render_last_view')

    query = Video.objects.filter(
        Q(encoding_in_progress=False)
        & Q(is_draft=False)
        & Q(sites=current_site)
    )

    query = addfilter(params, debugElts, query)

    last_viewed_videos = query.all()[:int(params['nb-element'])]

    debugElts.append(f"Database query '{str(last_viewed_videos.query)}'")

    debugElts.append('Found videos in container :')

    for video in last_viewed_videos:
        debugElts.append(f' - Video informations : '
                         f'[ID:{video.id}] [SLUG:{video.slug}] [RECENT_VIW_COUNT:{video.recentViewcount}]')

    if last_viewed_videos.count() < params['slider-multi-nb-card']:
        params['slider-multi-nb-card'] = last_viewed_videos.count()

    if (params['title'] == ''):
        title = 'Les dernières vidéos'
    else:
        title = params['title']

    part_content = loader.get_template(params['template']).render(
        {
            "uniq_id": uniq_id,
            "title" : title,
            "type": 'last',
            "elements" : last_viewed_videos,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']
        }
    )
    return part_content


def addfilter(params, debugElts, data):
    if not params['show-restricted']:
        data = data.filter(is_restricted=False)
        debugElts.append('apply filter not show restricted')

    if not params['view-videos-from-non-visible-channels']:
        data = data.exclude(channel__visible=0)
        debugElts.append('apply filter not show videos non visible channels')

    if not params['show-passworded']:
        data = data.filter(Q(password="") | Q(password__isnull=True))
        debugElts.append('apply filter not show videos password')

    return data


def debugFile(str):
    f = open("/home/pod/debugJM.log", "a")
    f.write("%s\n" % (str))
    f.close()
