"""
pod_project URL Configuration
"""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.apps import apps
from django.contrib.auth import views as auth_views

from pod.authentication.views import authentication_login
from pod.authentication.views import authentication_logout
from pod.authentication.views import authentication_login_gateway

from pod.video.views import video
from pod.video.views import video_edit
from pod.video.views import video_delete
from pod.video.views import channel
from pod.video.views import videos
from pod.video.views import my_videos
from pod.video.views import my_channels
from pod.video.views import channel_edit
from pod.video.views import theme_edit
from pod.main.views import contact_us


if apps.is_installed('pod.filepicker'):
    from pod.filepicker.sites import site as filepicker_site

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # Translation
    url(r'^i18n/', include('django.conf.urls.i18n')),
    # progressbar
    url(r'^progressbarupload/', include('progressbarupload.urls')),

    # App video
    url(r'^videos/$', videos, name='videos'),
    url(r'^video/(?P<slug>[\-\d\w]+)/$', video, name='video'),
    url(r'^video/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$', video,
        name='video_private'),
    url(r'^video_edit/$', video_edit, name='video_edit'),
    url(r'^video_edit/(?P<slug>[\-\d\w]+)/$', video_edit, name='video_edit'),
    url(r'^video_delete/(?P<slug>[\-\d\w]+)/$',
        video_delete, name='video_delete'),
    # my channels
    url(r'^my_channels/$', my_channels, name='my_channels'),
    url(r'^channel_edit/(?P<slug>[\-\d\w]+)/$',
        channel_edit, name='channel_edit'),
    url(r'^theme_edit/(?P<slug>[\-\d\w]+)/$', theme_edit, name='theme_edit'),
    # my videos
    url(r'^my_videos/$', my_videos, name='my_videos'),

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
    url(r'^sso-cas/', include('django_cas.urls')),

    # contact_us
    url(r'^contact_us/$', contact_us, name='contact_us'),
    url(r'^captcha/', include('captcha.urls')),
]

if apps.is_installed('pod.filepicker'):
    urlpatterns += [url(r'^file-picker/', include(filepicker_site.urls)), ]
if apps.is_installed('pod.completion'):
    urlpatterns += [url(r'^', include('pod.completion.urls')), ]
if apps.is_installed('pod.chapters'):
    urlpatterns += [url(r'^', include('pod.chapters.urls')), ]

urlpatterns += [
    url(r'^(?P<slug_c>[\-\d\w]+)/$', channel, name='channel'),
    # url(r'^(?P<slug_c>[\-\d\w]+)/edit$',
    #    'pods.views.channel_edit', name='channel_edit'),
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
