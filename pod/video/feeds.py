from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from datetime import datetime
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.shortcuts import get_object_or_404

from pod.video.views import get_videos_list

from pod.video.models import EncodingAudio
from pod.video.models import Channel
from pod.video.models import Theme

import re
import os


##
# Settings exposed in templates
#
TEMPLATE_VISIBLE_SETTINGS = getattr(
    settings,
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

TITLE_ETB = TEMPLATE_VISIBLE_SETTINGS['TITLE_ETB'] if (
    TEMPLATE_VISIBLE_SETTINGS.get('TITLE_ETB')) else 'University name'
TITLE_SITE = TEMPLATE_VISIBLE_SETTINGS['TITLE_SITE'] if (
    TEMPLATE_VISIBLE_SETTINGS.get('TITLE_SITE')) else 'Pod'
LOGO_SITE = TEMPLATE_VISIBLE_SETTINGS['LOGO_SITE'] if (
    TEMPLATE_VISIBLE_SETTINGS.get('LOGO_SITE')) else 'img/logoPod.svg'

CONTACT_US_EMAIL = getattr(
    settings,
    'CONTACT_US_EMAIL',
    [mail for name, mail in getattr(settings, 'MANAGERS')])

DEFAULT_DC_COVERAGE = getattr(
    settings, 'DEFAULT_DC_COVERAGE', TITLE_ETB + " - Town - Country")
DEFAULT_DC_RIGHTS = getattr(settings, 'DEFAULT_DC_RIGHT', "BY-NC-SA")


class RssFeedGenerator(Rss201rev2Feed):

    def rss_attributes(self):
        return {
            'version': self._version,
            'xmlns:atom': 'http://www.w3.org/2005/Atom',
            'xmlns:itunes': u'http://www.itunes.com/dtds/podcast-1.0.dtd'
        }

    def add_root_elements(self, handler):
        super(RssFeedGenerator, self).add_root_elements(handler)
        handler.startElement(u'image', {})
        handler.addQuickElement(u"url", self.feed['image_url'])
        handler.addQuickElement(u"title", self.feed['title'])
        handler.addQuickElement(u"link", self.feed['link'])
        handler.endElement(u'image')

        handler.addQuickElement('itunes:subtitle', self.feed['subtitle'])
        handler.addQuickElement('itunes:author', self.feed['author_name'])
        handler.addQuickElement('itunes:summary', self.feed['description'])
        handler.startElement(
            'itunes:category', {'text': self.feed['iTunes_category']['text']})
        handler.addQuickElement(
            'itunes:category',
            '',
            {'text': self.feed['iTunes_category']['sub']})
        handler.endElement('itunes:category')
        handler.addQuickElement('itunes:explicit',
                                self.feed['iTunes_explicit'])
        handler.startElement("itunes:owner", {})
        handler.addQuickElement('itunes:name', self.feed['iTunes_name'])
        handler.addQuickElement('itunes:email', self.feed['iTunes_email'])
        handler.endElement("itunes:owner")
        handler.addQuickElement(
            'itunes:image', '', {'href': self.feed['image_url']})

    def add_item_elements(self, handler, item):
        super(RssFeedGenerator, self).add_item_elements(handler, item)
        handler.addQuickElement(u'itunes:subtitle', item['title'])
        handler.addQuickElement(u'itunes:summary', item['description'])
        handler.addQuickElement(u'itunes:duration', item['duration'])
        handler.addQuickElement(u'itunes:explicit', item['explicit'])


class RssSiteVideosFeed(Feed):
    title = TITLE_SITE
    link = "/videos/rss/"
    feed_url = '/videos/rss/'
    description = "%s %s %s" % (TITLE_SITE, _("video platform of"), TITLE_ETB)
    author_name = TITLE_ETB
    author_email = CONTACT_US_EMAIL[0]
    categories = ["Education"]
    author_link = ''
    feed_type = RssFeedGenerator
    feed_copyright = DEFAULT_DC_COVERAGE + " " + DEFAULT_DC_RIGHTS

    def feed_extra_kwargs(self, obj):
        return {
            'image_url': ''.join([settings.STATIC_URL, LOGO_SITE]),
            'iTunes_category': {'text': 'Education',
                                'sub': 'Higher Education'},
            'iTunes_explicit': 'clean',
            'iTunes_name': self.author_name,
            'iTunes_email': self.author_email
        }

    def item_extra_kwargs(self, item):
        return {
            'summary': item.description,
            'duration': item.duration_in_time,
            'explicit': 'clean',
        }

    def get_object(self, request, slug_c=None, slug_t=None):
        prefix = 'https://' if request.is_secure() else 'http://'
        self.author_link = ''.join([prefix, get_current_site(request).domain])
        self.link = request.get_full_path().replace(
            "rss-audio", "").replace("rss-video", "")
        self.feed_url = request.build_absolute_uri()

        videos_list = get_videos_list(request)

        if slug_c:
            channel = get_object_or_404(Channel, slug=slug_c,
                                        sites=get_current_site(request))
            self.subtitle = "%s" % (channel.title)
            videos_list = videos_list.filter(channel=channel)
            self.link = reverse('channel', kwargs={'slug_c': channel.slug})

            theme = None
            if slug_t:
                theme = get_object_or_404(Theme, channel=channel, slug=slug_t)
                self.subtitle = "%s of %s" % (
                    theme.title, theme.channel.title)
                list_theme = theme.get_all_children_flat()
                videos_list = videos_list.filter(theme__in=list_theme)
                self.link = reverse(
                    'theme', kwargs={
                        'slug_c': theme.channel.slug,
                        'slug_t': theme.slug})

        return videos_list

    def items(self, obj):
        return obj.order_by('-date_added')[:30]

    def item_title(self, item):
        return "%s | %s" % (item.owner, item.title)

    def item_link(self, item):
        return ''.join([self.author_link, item.get_absolute_url()])

    def item_author_name(self, item):
        return item.owner.get_full_name()

    def item_author_email(self, item):
        return item.owner.email

    def item_author_link(self, item):
        return ''.join([
            self.author_link,
            reverse('videos'),
            "?owner=%s" % item.owner.username])

    def item_description(self, item):
        description = "%s<br/>" % item.get_thumbnail_admin
        sub = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', item.description)
        # use re sub to remove Control characters are not supported in XML 1.0
        description += sub  # item.description
        description += "<br/> %s : %s" % (_('Duration'), item.duration_in_time)
        return description

    def item_pubdate(self, item):
        return datetime.strptime(
            item.date_added.strftime('%Y-%m-%d'), '%Y-%m-%d')

    def item_updateddate(self, item):
        return datetime.strptime(
            item.date_added.strftime('%Y-%m-%d'), '%Y-%m-%d')

    def item_enclosure_url(self, item):
        if (item.password is not None) or item.is_restricted:
            return ""
        if item.get_video_mp4().count() > 0:
            mp4 = sorted(item.get_video_mp4(), key=lambda m: m.height)[0]
            return ''.join([self.author_link, mp4.source_file.url])
        elif item.get_video_m4a():
            return ''.join([
                self.author_link,
                item.get_video_m4a().source_file.url])
        return ""

    def item_enclosure_mime_type(self, item):
        if item.get_video_mp4().count() > 0 or item.get_video_m4a():
            return "video/mp4"
        return ""

    def item_enclosure_length(self, item):
        if item.get_video_mp4().count() > 0:
            mp4 = sorted(item.get_video_mp4(), key=lambda m: m.height)[0]
            return mp4.source_file.size if (
                os.path.isfile(mp4.source_file.path)) else 0
        elif item.get_video_m4a():
            return item.get_video_m4a().source_file.size if (
                os.path.isfile(item.get_video_m4a().source_file.path)) else 0
        return ""

    def item_categories(self, item):
        return (item.type,)

    def item_copyright(self, obj):
        return obj.licence


class RssSiteAudiosFeed(RssSiteVideosFeed):

    def item_enclosure_url(self, item):
        try:
            mp3 = EncodingAudio.objects.get(
                name="audio", video=item, encoding_format="audio/mp3")
            if (item.password is not None) or item.is_restricted:
                return ""
            return ''.join([self.author_link, mp3.source_file.url])
        except EncodingAudio.DoesNotExist:
            return ""

    def item_enclosure_mime_type(self, item):
        try:
            return "audio/mpeg"
        except EncodingAudio.DoesNotExist:
            return ""

    def item_enclosure_length(self, item):
        try:
            mp3 = EncodingAudio.objects.get(
                name="audio", video=item, encoding_format="audio/mp3")
            return mp3.source_file.size if (
                os.path.isfile(mp3.source_file.path)) else 0
        except EncodingAudio.DoesNotExist:
            return ""
