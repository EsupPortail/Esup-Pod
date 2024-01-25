"""Esup-Pod video custom filters."""
from django import template
from html.parser import HTMLParser

from django.db.models import Prefetch, Count, F, Value
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from pod.playlist.models import PlaylistContent
from pod.video.models import Channel
from pod.video.models import Theme
from pod.video.models import Video
from pod.live.models import Event
from django.db.models import Q, Sum
from django.template import loader
from datetime import date, datetime, timedelta
from django.conf import settings
from django.utils import timezone

import html
import re
import random
import string
import hashlib

register = template.Library()
parser = HTMLParser()
html_parser = html

#helpers
#https://pythex.org/
# <!-- EDITO:SLIDER type="theme" slug="a-la-une"-->
# <!-- EDITO:SLIDER_MULTI type="theme" slug="a-la-une"-->
# <!-- EDITO:MOST_VIEW nb-element="5" -->
# <!-- EDITO:NEXT_EVENTS nb-element="5" -->
# <!-- EDITO:CARD_LIST type="theme" slug="luniverstie-de-lorraine" -->
# <!-- EDITO:CARD_LIST type="theme" slug="vie-des-campus" -->
# <!-- EDITO:CARD_LIST type="theme" slug="la-recherche-a-luniversite-de-lorraine" -->
# <!-- EDITO:CARD_LIST type="theme" slug="nos-formations" -->
# <!-- EDITO:CARD_LIST type="channel" id="24" -->
#
# Additionnal params
#  title="Mon titre a moi" par défaut le titre de la chaine ou du thème
#  nb-element="10" par defaut 5 si non spécifié
#  mustbe-auth="true" par defaut true si non spécifié
#  show-restricted="true" par defaut false si non spécifié
#  debug="true" par defaut false si non spécifié
#  slider-multi-nb-card="5" nombre de card cote à cote a afficher
#  no-cache="true" par defaut true si non spécifié
# see more about filter https://books.agiliq.com/projects/django-orm-cookbook/en/latest/query.html
TYPE_LIST = [
    {'name': 'SLIDER', 'render_fct': 'render_base_videos', 'template': 'edito/slider.html'},  
    {'name': 'SLIDER_MULTI', 'render_fct': 'render_base_videos', 'template': 'edito/slider_multi.html'},    
    {'name': 'CARD_LIST', 'render_fct': 'render_base_videos', 'template': 'edito/card_list.html' },
    {'name': 'MOST_VIEW', 'render_fct': 'render_most_view', 'template': 'edito/card_list.html' },
    {'name': 'MOST_VIEW_SLIDER', 'render_fct': 'render_most_view', 'template': 'edito/slider.html' },    
    {'name': 'MOST_VIEW_SLIDER_MULTI', 'render_fct': 'render_most_view', 'template': 'edito/slider_multi.html' },
    {'name': 'NEXT_EVENTS', 'render_fct': 'render_next_events', 'template': 'edito/card_list.html' }, 
    {'name': 'NEXT_EVENTS_SLIDER', 'render_fct': 'render_next_events', 'template': 'edito/slider.html' },  
    {'name': 'NEXT_EVENTS_SLIDER_MULTI', 'render_fct': 'render_next_events', 'template': 'edito/slider_multi.html' },      
]

VIDEO_RECENT_VIEWCOUNT = getattr(settings, "VIDEO_RECENT_VIEWCOUNT", 180)
EDITO_CACHE_TIMEOUT = getattr(settings, "EDITO_CACHE_TIMEOUT", 300)
EDITO_CACHE_PREFIX = getattr(settings, "EDITO_CACHE_PREFIX", "edito_cache_")

@register.filter(name="edito")
def edito(content, request):
    bloc = findTypeInContent(content, request)
    return bloc
    
def findTypeInContent(content, request):
        
    debugElts=[]

    md5_part = hashlib.md5(str(content).encode('utf-8')).hexdigest()

    params = dict()

    if(content.debug == True):
        params['debug'] = True
    if(content.debug == False):
        params['debug'] = False

    if('debug' in request.GET):
        if(request.GET['debug'] == True):
            params['debug'] = True
        
    if(content.no_cache == True):
        params['cache'] = False
        if(params['debug']):
            debugElts.append('Cache is enable for this part')
    if(content.no_cache == False):
        params['cache'] = True
        if(params['debug']): 
            debugElts.append('Cache is disable for this part')
        
    if(content.nb_element is not None or content.nb_element != ""):
        params['nb-element'] = int(content.nb_element)
    else:
        params['nb-element'] = 5
        
    if(content.slider_multi_nb is not None or content.slider_multi_nb != ""):
        params['slider-multi-nb-card'] = int(content.slider_multi_nb)
    else:
        params['slider-multi-nb-card'] = 5
        
    if(content.title is not None):
        params['title'] = content.title
    else:
        params['title'] = ""

    if(content.show_restricted == True):
        params['show-restricted'] = True
    if(content.show_restricted == False):
        params['show-restricted'] = False

    if(content.must_be_auth == True):
        params['mustbe-auth'] = True
    if(content.must_be_auth == False):
        params['mustbe-auth'] = False
        
    if(content.auto_slide == True):
        params['auto-slide'] = True
    if(content.auto_slide == False):
        params['auto-slide'] = False

    if(content.data_type == 'channel'):
        params['fct'] = 'render_base_videos'
        params['type'] = 'channel'
        params['data'] = content.Channel

    if(content.data_type == 'theme'):
        params['fct'] = 'render_base_videos'
        params['type'] = 'theme'
        params['data'] = content.Theme

    if(content.data_type == 'playlist'):
        params['fct'] = 'render_base_videos'
        params['type'] = 'playlist'
        params['data'] = content.Playlist

    if(content.data_type == 'event_next'):
        params['fct'] = 'render_next_events'
        params['type'] = 'event'

    if(content.data_type == 'most_views'):
        params['fct'] = 'render_most_view'
        params['type'] = 'event'

    if(content.type == 'html'):
        params['template'] = 'bloc/html.html'
        params['fct'] = 'render_html'
        params['data'] = content.html

    if(content.type == 'slider'):
        params['template'] = 'bloc/slider.html'
    if(content.type == 'slider_multi'):
        params['template'] = 'bloc/slider_multi.html'
    if(content.type == 'card_list'):
        params['template'] = 'bloc/card_list.html'
        
    if((params['mustbe-auth'] == True) and (request.user.is_authenticated != True)):
        if(params['debug']): 
            debugElts.append('User is not authenticated and mustbe-auth=true hide result')
        content_part=''
        if(params['debug']): 
            content_part = "<pre>%s</pre>" %('\n'.join(debugElts))          
            content = content_part
    else:   
        if params['cache']:
            cached_content_part = cache.get(EDITO_CACHE_PREFIX+md5_part)
        else:
            cached_content_part=None
                
        if not cached_content_part:        
            if(params['debug']): 
                debugElts.append('Not found in cache')            
            uniq_id = ''.join(random.choice(string.ascii_letters) for i in range(20))
            content_part = globals()["%s" % params['fct']](uniq_id, params, content.data_type, debugElts)
            cache.set(EDITO_CACHE_PREFIX+md5_part, content_part, timeout=EDITO_CACHE_TIMEOUT)                     
        else:
            content_part = cached_content_part
            if(params['debug']): 
                debugElts.append('Found in cache')
                    
        if(params['debug']): 
            content_part = "<pre>%s</pre>%s" %('\n'.join(debugElts), content_part)
        content = content_part
           
    return(content)

def render_base_videos(uniq_id, params, type, debugElts):
    if(params['debug']): 
        debugElts.append('Call function render_base_videos')
  
    container = params['data']
        
    filters = {}

    if(params['type'] == 'playlist'):
        container_childrens = PlaylistContent.objects.filter(
            playlist = params['data']
        )
        container_playlist = []
        for list in container_childrens:
            container_playlist.append(list.video.id)
        filters["id__in"] = container_playlist
    else:
        if(params['type'] == "theme"):
            container_childrens = container.get_all_children_flat()
            filters["theme__in"] = container_childrens
            if(params['debug']): 
                if(len(container_childrens) > 1):
                    debugElts.append('Theme has children(s)')
                    for children in container_childrens:
                        debugElts.append(' - children found [ID:%s] [SLUG:%s] [TITLE:%s]'%(children.id, children.slug, children.title))
        else:
            filters[params['type']] = container

    filters['encoding_in_progress'] = False
    filters['is_draft'] = False
        
    if(params['show-restricted'] == False):
        filters['is_restricted'] = False            
        
    filter_q = Q(**filters)

    initial_list = Video.objects.filter(
        filter_q & (Q(password="") | Q(password__isnull=True))
    ).defer(
        "video", "slug", "description"
    ).distinct()[:int(params['nb-element'])]
      
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(initial_list.query)))
    
    videos_list={'list': [], 'count': 0}
    
    if(params['debug']): 
        debugElts.append('Finded videos in container :')
    
    for video in initial_list:
        if(params['debug']): 
            debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s]'%(video.id, video.slug, video.title))
        videos_list['list'].append(video)
        videos_list['count'] = videos_list['count'] + 1
        if(videos_list['count'] >= int(params['nb-element'])):
            break
    
    if(params['title'] == ''):
        title=container.title
    else:
        title=params['title']
    
    if(videos_list['count'] < params['slider-multi-nb-card']):
        params['slider-multi-nb-card'] = videos_list['count']
        
    part_content = loader.get_template(params['template']).render(
        {
            "uniq_id": uniq_id,
            "container": container,
            "title" : title,
            "videos_list" : videos_list,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']  
        }
    )
    return "%s" %(part_content)
    
def render_most_view(uniq_id, params, type, debugElts):
    if(params['debug']): 
        debugElts.append('Call function render_most_view')
    
    d = date.today() - timezone.timedelta(days=VIDEO_RECENT_VIEWCOUNT)
    query = Video.objects.filter(
        Q(encoding_in_progress=False)
        & Q(is_draft=False)
        & (Q(password="") | Q(password__isnull=True))
        & Q(viewcount__date__gte=d)
    ).annotate(nombre=Sum('viewcount'))
    
    if not params['show-restricted']:
        query.filter(is_restricted=False)

    most_viewed_videos = query.all().order_by('nombre')[:int(params['nb-element'])]
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(most_viewed_videos.query)))
        
    videos_list = {'list': most_viewed_videos, 'count': most_viewed_videos.count()}
    if(params['debug']): 
       debugElts.append('Finded videos in container :')
    
    for video in most_viewed_videos:    
        if(params['debug']): 
           debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s] [RECENT_VIW_COUNT:%s]'%(video.id, video.slug, video.title, video.recentViewcount))

    part_content = loader.get_template(params['template']).render(
        {   
            "uniq_id": uniq_id,
            "title" : params['title'],
            "videos_list" : videos_list,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']  
        }
    )
    return "%s" %(part_content)
    
def render_next_events(uniq_id, params, type, debugElts):    
    if(params['debug']): 
        debugElts.append('Call function render_next_events')
        
    initial_list = Event.objects.filter(
        Q(start_date__gt=date.today())
        | (Q(start_date=date.today()) & Q(end_date__gte=datetime.now()))
    )
    initial_list = initial_list.filter(is_draft=False)
    
    if(params['show-restricted'] == False):
        initial_list = initial_list.filter(is_restricted=False)
    
    initial_list = initial_list.all().order_by("start_date")
    
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(initial_list.query)))
        
    if(params['debug']): 
        debugElts.append('Finded videos in container :')
    
    videos_list={'list': [], 'count': 0}
    for video in initial_list:
        if(params['debug']): 
            debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s]'%(video.id, video.slug, video.title))
        videos_list['list'].append(video)
        videos_list['count'] = videos_list['count'] + 1
        if(videos_list['count'] >= int(params['nb-element'])):
            break
            
    part_content = loader.get_template(params['template']).render(
        {   
            "uniq_id" : uniq_id,
            "title" : params['title'],
            "videos_list" : videos_list,
            "nb_element": params['nb-element'],
            "auto_slide": params['auto-slide'],
            "slider_multi_nb_card" : params['slider-multi-nb-card']            
        }
    )
    return "%s" %(part_content)
    
def render_html(uniq_id, params, type, debugElts):
    if(params['debug']): 
        debugElts.append('Call function render_html')
            
    part_content = loader.get_template(params['template']).render(
        {   
            "body": params['data'] 
        }
    )
    return "%s" %(part_content)
   
def debugFile(str):
    f = open("/home/pod/debugJM.log", "a")
    f.write("%s\n" % (str))
    f.close()