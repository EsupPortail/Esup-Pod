# -*- coding: utf-8 -*-
"""
Copyright (C) 2014 Nicolas Can
Ce programme est un logiciel libre : vous pouvez
le redistribuer et/ou le modifier sous les termes
de la licence GNU Public Licence telle que publiée
par la Free Software Foundation, soit dans la
version 3 de la licence, ou (selon votre choix)
toute version ultérieure.
Ce programme est distribué avec l'espoir
qu'il sera utile, mais SANS AUCUNE
GARANTIE : sans même les garanties
implicites de VALEUR MARCHANDE ou
D'APPLICABILITÉ À UN BUT PRÉCIS. Voir
la licence GNU General Public License
pour plus de détails.
Vous devriez avoir reçu une copie de la licence
GNU General Public Licence
avec ce programme. Si ce n'est pas le cas,
voir http://www.gnu.org/licenses/
"""
from __future__ import unicode_literals

from django.template import Library
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
from pods.models import Channel, Pod, Playlist, PlaylistVideo

register = Library()

DOT = '.'
PAGE_VAR = 'page'
HOMEPAGE_SHOWS_PASSWORDED = getattr(settings, 'HOMEPAGE_SHOWS_PASSWORDED', True)
HOMEPAGE_SHOWS_RESTRICTED = getattr(settings, 'HOMEPAGE_SHOWS_RESTRICTED', True)
HOMEPAGE_NBR_CONTENTS_SHOWN = getattr(settings, 'HOMEPAGE_NBR_CONTENTS_SHOWN', 12)




@register.inclusion_tag("channels/channels_list.html")
def get_official_channels():
    return {
        'channels': Channel.objects.filter(id__lt=9).exclude(
            visible=0).order_by('id').distinct().annotate(video_count=Count("pod", distinct=True)),
        'DEFAULT_IMG': settings.DEFAULT_IMG
    }

@register.inclusion_tag("playlists/playlist_carousel.html")
def get_carousel_playlist():
    info = Playlist.objects.get(id=1)
    videos = PlaylistVideo.objects.filter(playlist=info)
    playlist = {
         'info': info,
         'videos': videos
    }
    return {
        'playlist': playlist,
    }
