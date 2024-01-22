"""Esup-Pod video custom filters."""
from django import template
from html.parser import HTMLParser

from django.db.models import Prefetch, Count, F, Value
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
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
        params['debug'] = 'true'
    if(content.debug == False):
        params['debug'] = 'false'

    if('debug' in request.GET):
        if(request.GET['debug'] == 'true'):
            params['debug'] = True
    
    # if(params['debug']): 
    #     debugElts.append('Debug is activated for %s' %(m.replace("<", "&lt;").replace(">", "&gt;")))
    #     debugElts.append('MD5 calculated for part %s' %(md5_part))
    #     debugElts.append('Type definition :')
    #     for t in type: 
    #         debugElts.append('  - %s=%s' % (t, str(type[t])))
    #         debugElts.append('Params find :')
    #         for p in params: 
    #             debugElts.append('  - %s=%s' % (p, str(params[p])))
        
    if(content.no_cache == True):
        params['cache'] = 'true'
    if(content.no_cache == False):
        params['cache'] = 'false'
        if(params['debug']): 
            debugElts.append('Cache is disable for this part') 
        else:
            params['cache'] = True
            if(params['debug']): 
                debugElts.append('Cache is enable for this part')
        
        if('nb-element' not in params):
            params['nb-element'] = 5
            if(params['debug']): 
                debugElts.append('Param nb-element not defined use default value %s' %(params['nb-element']))            
        params['nb-element'] = int(params['nb-element'])
        
        if('slider-multi-nb-card' not in params):
            params['slider-multi-nb-card'] = 5
            if(params['debug']): 
                debugElts.append('Param slider-multi-nb-card not defined use default value %s' %(params['slider-multi-nb-card']))
        params['slider-multi-nb-card'] = int(params['slider-multi-nb-card'])
        
        if('title' not in params):
            params['title'] = ''
            if(params['debug']): 
                debugElts.append('Param title not defined use default value %s' %(params['title']))
        
        if(content.show_restricted == True):
            params['show_restricted'] = 'true'
        if(content.show_restricted == False):
            params['show_restricted'] = 'false'
        if('show-restricted' not in params):
            params['show-restricted'] = 'false'
            if(params['debug']): 
                debugElts.append('Param show-restricted not defined use default value %s' %(params['show-restricted']))
            
        if('mustbe-auth' not in params):
            params['mustbe-auth'] = 'true'
            if(params['debug']): 
                debugElts.append('Param mustbe-auth not defined use default value %s' %(params['mustbe-auth']))            
            
        if(params['mustbe-auth'].lower() == 'true'):
            params['mustbe-auth'] = True
        else:
            params['mustbe-auth'] = False
        
        if('auto-slide' not in params):
            params['auto-slide'] = 'true'
            if(params['debug']): 
                debugElts.append('Param auto-slide not defined use default value %s' %(params['auto-slide']))            
        if(params['auto-slide'].lower() == 'true'):
            params['auto-slide'] = True
        else:
            params['auto-slide'] = False

        if(content.data_type == 'channel'):
            params['fct'] = 'render_base_videos'
            params['type'] = 'channel'
            params['id'] = content.Channel

        if(content.type == 'slider'):
            params['template'] = 'bloc/slider.html'
        
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
  
    if('type' in params and params['type'] == 'theme'):
        if('id' in params):
            if(Theme.objects.filter(id=params['id']).exists()):
                container = Theme.objects.get(id=params['id'])
            else:
                return("ERROR:theme with id %s not found" % params['id'])  
        elif('slug' in params):
            if(Theme.objects.filter(slug=params['slug']).exists()):
                count_theme = len(Theme.objects.filter(slug=params['slug']))
                if(count_theme > 1):
                    return("ERROR:Find more than 1 theme with slug \"%s\"" %(params['slug']))
                container = Theme.objects.get(slug=params['slug'])                
            else:
                return("ERROR:theme with slug %s not found" % params['slug'])    
    elif(params['type'] == 'channel'):
        if('id' in params):
            container = params['id']
        elif('slug' in params):
            container = Channel.objects.get(slug=params['slug'])
        else:
            return("ERROR:parameter id or slug is missing")
    else:
        return("ERROR:parameter type [theme|channel] is missing")

    if(params['debug']): 
        debugElts.append('Video container is a \"%s\" informations is [ID:%s] [SLUG:%s] [TITLE:%s]'%(params['type'], container.id, container.slug, container.title))
        
    filters = {}
    
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
    
    inital_list = Video.objects.filter(
        filter_q & (Q(password="") | Q(password__isnull=True))
    ).defer(
        "video", "slug", "description"
    ).distinct()[:int(params['nb-element'])]
      
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(inital_list.query)))
        
    #Intégration au filter initial filter_q & (Q(password="") | Q(password__isnull=True))
    # inital_list = inital_list.filter(Q(password="") | Q(password__isnull=True))
    
    videos_list={'list': [], 'count': 0}
    
    if(params['debug']): 
        debugElts.append('Finded videos in container :')
    
    for video in inital_list:
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
    # if(params['debug']): 
        # debugElts.append('Use template %s'%(type['template']))
        # debugElts.append('Template content rendered :')
        # debugElts.append('%s'%(html.escape(part_content)))
        # debugElts.append('END Template content rendered')
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

    most_viewed_videos = query.all().order_by('-nombre')[:int(params['nb-element'])]
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(most_viewed_videos.query)))
        
    videos_list = {'list': most_viewed_videos, 'count': most_viewed_videos.count()}
    if(params['debug']): 
       debugElts.append('Finded videos in container :')
    
    for video in most_viewed_videos:    
        if(params['debug']): 
           debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s] [RECENT_VIW_COUNT:%s]'%(video.id, video.slug, video.title, video.recentViewcount))
       
    #####
    #filters = {}
    #filters['encoding_in_progress'] = False
    #filters['is_draft'] = False
    #
    #if(params['show-restricted'] == False):
    #    filters['is_restricted'] = False
    #
    #filter_q = Q(**filters)
    #
    #inital_list = Video.objects.filter(
    #    filter_q & (Q(password="") | Q(password__isnull=True))
    #).defer(
    #    "video", "slug", "description"
    #)[:int(params['nb-element'])]
    #
    #if(params['debug']): 
    #    debugElts.append('Database query \"%s\"'%(str(inital_list.query)))
    #    
    #inital_list = sorted(inital_list, key=lambda x: x.recentViewcount, reverse=True)
    #
    #if(params['debug']): 
    #    debugElts.append('Finded videos in container :')
    #
    #videos_list={'list': [], 'count': 0}
    #for video in inital_list:
    #    if(params['debug']): 
    #        debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s] [RECENT_VIW_COUNT:%s]'%(video.id, video.slug, video.title, video.recentViewcount))
    #    videos_list['list'].append(video)
    #    videos_list['count'] = videos_list['count'] + 1
    #    if(videos_list['count'] >= int(params['nb-element'])):
    #        break
            
    part_content = loader.get_template(type['template']).render(
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
        
    inital_list = Event.objects.filter(
        Q(start_date__gt=date.today())
        | (Q(start_date=date.today()) & Q(end_date__gte=datetime.now()))
    )[:20]
    inital_list = inital_list.filter(is_draft=False)
    
    if(params['show-restricted'] == False):
        inital_list = inital_list.filter(is_restricted=False)
    
    inital_list = inital_list.all().order_by("start_date")
    
    if(params['debug']): 
        debugElts.append('Database query \"%s\"'%(str(inital_list.query)))
        
    if(params['debug']): 
        debugElts.append('Finded videos in container :')
    
    videos_list={'list': [], 'count': 0}
    for video in inital_list:
        if(params['debug']): 
            debugElts.append(' - Video informations is [ID:%s] [SLUG:%s] [TITLE:%s]'%(video.id, video.slug, video.title))
        videos_list['list'].append(video)
        videos_list['count'] = videos_list['count'] + 1
        if(videos_list['count'] >= int(params['nb-element'])):
            break
            
    part_content = loader.get_template(type['template']).render(
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
    

   
def debugFile(str):
    f = open("/home/pod/debugJM.log", "a")
    f.write("%s\n" % (str))
    f.close()