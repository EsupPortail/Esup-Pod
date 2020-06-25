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
from pod.video.views import video_add
from pod.video.views import video_delete
# from pod.video.views import video_collaborate
from pod.video.views import channel
from pod.video.views import videos
from pod.video.views import my_videos
from pod.video.views import my_channels
from pod.video.views import channel_edit
from pod.video.views import theme_edit
from pod.video.views import video_notes
from pod.video.views import video_count, video_version
from pod.video.views import video_oembed
from pod.video.views import stats_view
from pod.video.feeds import RssSiteVideosFeed, RssSiteAudiosFeed
from pod.main.views import contact_us, download_file, user_autocomplete
from pod.main.rest_router import urlpatterns as rest_urlpatterns
from pod.video_search.views import search_videos
from pod.recorder.views import add_recording, recorder_notify, claim_record,\
    delete_record
from pod.lti.views import LTIAssignmentAddVideoView, LTIAssignmentGetVideoView
from pod.video.views import PodChunkedUploadView, PodChunkedUploadCompleteView

USE_CAS = getattr(
    settings, 'USE_CAS', False)
USE_SHIB = getattr(
    settings, 'USE_SHIB', False)
OEMBED = getattr(
    settings, 'OEMBED', False)

if USE_CAS:
    from cas import views as cas_views

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
    url(r'^video_add/$', video_add, name='video_add'),
    url(r'^video_edit/$', video_edit, name='video_edit'),
    url(r'^video_edit/(?P<slug>[\-\d\w]+)/$', video_edit, name='video_edit'),
    url(r'^video_delete/(?P<slug>[\-\d\w]+)/$',
        video_delete, name='video_delete'),
    url(r'^video_notes/(?P<slug>[\-\d\w]+)/$',
        video_notes, name='video_notes'),
    url(r'^video_count/(?P<id>[\d]+)/$',
        video_count, name='video_count'),
    url(r'^video_version/(?P<id>[\d]+)/$',
        video_version, name='video_version'),

    # url(r'^video_collaborate/(?P<slug>[\-\d\w]+)/$',
    #    video_collaborate,
    #    name='video_collaborate'),

    url('api/chunked_upload_complete/', PodChunkedUploadCompleteView.as_view(),
        name='api_chunked_upload_complete'),
    url('api/chunked_upload/', PodChunkedUploadView.as_view(),
        name='api_chunked_upload'),

    url(r'^ajax_calls/search_user/', user_autocomplete),
    # my channels
    url(r'^my_channels/$', my_channels, name='my_channels'),
    url(r'^channel_edit/(?P<slug>[\-\d\w]+)/$',
        channel_edit, name='channel_edit'),
    url(r'^theme_edit/(?P<slug>[\-\d\w]+)/$', theme_edit, name='theme_edit'),
    # my videos
    url(r'^my_videos/$', my_videos, name='my_videos'),
    # recording
    url(r'^add_recording/$', add_recording, name='add_recording'),
    url(r'^recorder_notify/$', recorder_notify, name='recorder_notify'),
    url(r'^claim_record/$', claim_record, name='claim_record'),
    url(r'^delete_record/(?P<id>[\d]+)/$', delete_record,
        name='delete_record'),

    url(r'^search/$', search_videos, name='search_videos'),

    # auth cas
    url(r'^authentication_login/$',
        authentication_login, name='authentication_login'),
    url(r'^authentication_logout/$',
        authentication_logout, name='authentication_logout'),
    url(r'^authentication_login/$',
        authentication_login, name='login'),
    url(r'^authentication_logout/$',
        authentication_logout, name='logout'),
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

    # django-select2-form
    url(r'^select2/', include('select2.urls')),

    # custom
    url(r'^custom/', include('pod.custom.urls')),
]
# CAS
if USE_CAS:
    # urlpatterns += [url(r'^sso-cas/', include('cas.urls')), ]
    urlpatterns += [
        url(r'^sso-cas/login/$', cas_views.login, name='cas-login'),
        url(r'^sso-cas/logout/$', cas_views.logout, name='cas-logout'),
    ]


##
# OEMBED feature patterns
#
if OEMBED:
    urlpatterns += [url(r'^oembed/', video_oembed, name='video_oembed'), ]

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
        url(r'^assignment/addvideo/',
            LTIAssignmentAddVideoView.as_view()),
        url(r'^assignment/getvideo/',
            LTIAssignmentGetVideoView.as_view()),
    ]
##
# H5P feature patterns
#
if getattr(settings, 'H5P_ENABLED', False):
    urlpatterns += [
        url(r'^h5p/login/', authentication_login, name='h5p_login'),
        url(r'^h5p/logout/', authentication_logout, name='h5p_logout'),
        url(r'^h5p/', include('h5pp.urls')),
    ]

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns += [
        url(r'^video_stats_view/$', stats_view,
            name="video_stats_view"),
        url(r'^video_stats_view/(?P<slug>[-\w]+)/$', stats_view,
            name="video_stats_view"),
        url(r'^video_stats_view/(?P<slug>[-\w]+)/(?P<slug_t>[-\w]+)/$',
            stats_view, name='video_stats_view'),
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
