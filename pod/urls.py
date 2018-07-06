"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
from django.utils.translation import ugettext_lazy as _

from pod.authentication.views import authentication_login
from pod.authentication.views import authentication_logout
from pod.authentication.views import authentication_login_gateway
from pod.authentication.views import userpicture

from pod.video.views import video
from pod.video.views import video_edit
from pod.video.views import video_delete
from pod.video.views import channel
from pod.video.views import videos
from pod.video.views import my_videos
from pod.video.views import my_channels
from pod.video.views import channel_edit
from pod.video.views import theme_edit
from pod.video.views import video_notes
from pod.video.views import video_count
from pod.video.feeds import RssSiteVideosFeed, RssSiteAudiosFeed
from pod.main.views import contact_us, download_file
from pod.main.rest_router import urlpatterns as rest_urlpatterns
from pod.video_search.views import search_videos
from pod.recorder.views import add_recording
from pod.lti.views import LTIAssignmentView

USE_CAS = getattr(
    settings, 'USE_CAS', False)

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Translation
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    # progressbar
    url(r'^progressbarupload/', include('progressbarupload.urls')),

    # App video
    url(r'^videos/$', videos, name='videos'),

    url(r'^rss-video/$', RssSiteVideosFeed(), name='rss-video'),
    url(r'^rss-audio/$', RssSiteAudiosFeed(), name='rss-audio'),
    url(r'^rss-video/(?P<slug_c>[\-\d\w]+)/$',
        RssSiteVideosFeed(), name='rss-video'),
    url(r'^rss-audio/(?P<slug_c>[\-\d\w]+)/$',
        RssSiteAudiosFeed(), name='rss-audio'),
    url(r'^rss-video/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$',
        RssSiteVideosFeed(), name='rss-video'),
    url(r'^rss-audio/(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$',
        RssSiteAudiosFeed(), name='rss-audio'),

    url(r'^video/(?P<slug>[\-\d\w]+)/$', video, name='video'),
    url(r'^video/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$', video,
        name='video_private'),
    url(r'^video_edit/$', video_edit, name='video_edit'),
    url(r'^video_edit/(?P<slug>[\-\d\w]+)/$', video_edit, name='video_edit'),
    url(r'^video_delete/(?P<slug>[\-\d\w]+)/$',
        video_delete, name='video_delete'),
    url(r'^video_notes/(?P<id>[\d]+)/$',
        video_notes, name='video_notes'),
    url(r'^video_count/(?P<id>[\d]+)/$',
        video_count, name='video_count'),
    # my channels
    url(r'^my_channels/$', my_channels, name='my_channels'),
    url(r'^channel_edit/(?P<slug>[\-\d\w]+)/$',
        channel_edit, name='channel_edit'),
    url(r'^theme_edit/(?P<slug>[\-\d\w]+)/$', theme_edit, name='theme_edit'),
    # my videos
    url(r'^my_videos/$', my_videos, name='my_videos'),
    # recording
    url(r'^add_recording/$', add_recording, name='add_recording'),

    url(r'^search/$', search_videos, name='search_videos'),

    # auth cas
    url(r'^authentication_login/$',
        authentication_login, name='authentication_login'),
    url(r'^authentication_logout/$',
        authentication_logout, name='authentication_logout'),
    url(r'^authentication_login_gateway/$',
        authentication_login_gateway, name='authentication_login_gateway'),
    url(r'^accounts/login/$',
        auth_views.LoginView.as_view(),
        {'redirect_authenticated_user': True},
        name='local-login'),
    url(r'^accounts/logout/$',
        auth_views.LogoutView.as_view(),
        {'next_page': '/'},
        name='local-logout'),
    url(r'^accounts/change-password/$',
        auth_views.PasswordChangeView.as_view()),
    url(r'^accounts/reset-password/$',
        auth_views.PasswordResetView.as_view()),
    url(r'^accounts/userpicture/$', userpicture, name='userpicture'),
    # rest framework
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'^rest/', include(rest_urlpatterns)),

    # contact_us
    url(r'^contact_us/$', contact_us, name='contact_us'),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^download/$', download_file, name='download_file'),
]
# CAS
if USE_CAS:
    urlpatterns += [url(r'^sso-cas/', include('django_cas.urls')), ]
# APPS -> to change !
urlpatterns += [url(r'^', include('pod.completion.urls')), ]
urlpatterns += [url(r'^', include('pod.chapter.urls')), ]
urlpatterns += [url(r'^', include('pod.playlist.urls')), ]

if getattr(settings, 'USE_PODFILE', False):
    urlpatterns += [url(r'^podfile/', include('pod.podfile.urls')), ]

for apps in settings.THIRD_PARTY_APPS:
    urlpatterns += [url(r'^' + apps + '/', include('pod.%s.urls' % apps)), ]

##
# LTI feature patterns
#
if getattr(settings, 'LTI_ENABLED', False):
    # LTI href
    urlpatterns += [
        url(r'^lti/', include('lti_provider.urls')),
        url(r'^assignment/(?P<activity>[\-\d\w]+)/',
            LTIAssignmentView.as_view()),
    ]

# CHANNELS
urlpatterns += [
    url(r'^(?P<slug_c>[\-\d\w]+)/$', channel, name='channel'),
    url(r'^(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)/$',
        channel, name='theme'),
    url(r'^(?P<slug_c>[\-\d\w]+)/video/(?P<slug>[\-\d\w]+)/$',
        video, name='video'),
    url(r'^(?P<slug_c>[\-\d\w]+)/(?P<slug_t>[\-\d\w]+)'
        r'/video/(?P<slug>[\-\d\w]+)/$', video, name='video'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

# Change admin site title
admin.site.site_header = _("Pod Administration")
admin.site.site_title = _("Pod Administration")
