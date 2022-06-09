"""Esup-pod URL configuration."""

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

from pod.video.views import get_comments, get_children_comment
from pod.video.views import add_comment, delete_comment
from pod.video.views import vote_get, vote_post

from pod.video.views import video_oembed
from pod.video.views import channel
from pod.video.views import video
from pod.video.views import stats_view

from pod.main.views import (
    contact_us,
    download_file,
    user_autocomplete,
    maintenance,
    robots_txt,
)
from pod.main.rest_router import urlpatterns as rest_urlpatterns
from pod.video_search.views import search_videos
from pod.recorder.views import (
    add_recording,
    recorder_notify,
    claim_record,
    delete_record,
)

USE_CAS = getattr(settings, "USE_CAS", False)
USE_SHIB = getattr(settings, "USE_SHIB", False)
USE_OIDC = getattr(settings, "USE_OIDC", False)
USE_BBB = getattr(settings, "USE_BBB", False)

if USE_CAS:
    from cas import views as cas_views


urlpatterns = [
    url("select2/", include("django_select2.urls")),
    url("robots.txt", robots_txt),
    url(r"^admin/", admin.site.urls),
    # Translation
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^jsi18n/$", JavaScriptCatalog.as_view(), name="javascript-catalog"),

    # videos
    url(r"^videos/", include("pod.video.urls-videos")),
    url(r"^rss", include("pod.video.urls-rss")),
    url(r"^video/", include("pod.video.urls")),

    url(r"^ajax_calls/search_user/", user_autocomplete),

    # my channels
    url(r"^channels/", include("pod.video.urls-channels")),

    # recording
    url(r"^add_recording/$", add_recording, name="add_recording"),
    url(r"^recorder_notify/$", recorder_notify, name="recorder_notify"),
    url(r"^claim_record/$", claim_record, name="claim_record"),
    url(r"^delete_record/(?P<id>[\d]+)/$", delete_record, name="delete_record"),
    url(r"^search/$", search_videos, name="search_videos"),
    # auth cas
    url(
        r"^authentication_login/$",
        authentication_login,
        name="authentication_login",
    ),
    url(
        r"^authentication_logout/$",
        authentication_logout,
        name="authentication_logout",
    ),
    url(r"^authentication_login/$", authentication_login, name="login"),
    url(r"^authentication_logout/$", authentication_logout, name="logout"),
    url(
        r"^authentication_login_gateway/$",
        authentication_login_gateway,
        name="authentication_login_gateway",
    ),
    url(
        r"^accounts/login/$",
        auth_views.LoginView.as_view(),
        {"redirect_authenticated_user": True},
        name="local-login",
    ),
    url(
        r"^accounts/logout/$",
        auth_views.LogoutView.as_view(),
        {"next_page": "/"},
        name="local-logout",
    ),
    url(r"^accounts/change-password/$", auth_views.PasswordChangeView.as_view()),
    url(r"^accounts/reset-password/$", auth_views.PasswordResetView.as_view()),
    url(r"^accounts/userpicture/$", userpicture, name="userpicture"),
    # rest framework
    url(r"^api-auth/", include("rest_framework.urls")),
    url(r"^rest/", include(rest_urlpatterns)),
    # contact_us
    url(r"^contact_us/$", contact_us, name="contact_us"),
    url(r"^captcha/", include("captcha.urls")),
    url(r"^download/$", download_file, name="download_file"),
    # custom
    url(r"^custom/", include("pod.custom.urls")),
]
urlpatterns += (url(r"^maintenance/$", maintenance, name="maintenance"),)

# CAS
if USE_CAS:
    # urlpatterns += [url(r'^sso-cas/', include('cas.urls')), ]
    urlpatterns += [
        url(r"^sso-cas/login/$", cas_views.login, name="cas-login"),
        url(r"^sso-cas/logout/$", cas_views.logout, name="cas-logout"),
    ]

# OIDC
if USE_OIDC:
    urlpatterns += [
        url(r"^oidc/", include("mozilla_django_oidc.urls")),
    ]

# BBB
if getattr(settings, "USE_BBB", False):
    urlpatterns += [
        url(r"^bbb/", include("pod.bbb.urls")),
    ]

##
# OEMBED feature patterns
#
if getattr(settings, "OEMBED", False):
    urlpatterns += [
        url(r"^oembed/", video_oembed, name="video_oembed"),
    ]

if getattr(settings, "USE_OPENCAST_STUDIO", False):
    urlpatterns += [
        url(r"^studio/", include("pod.recorder.studio_urls")),
    ]

# APPS -> to change !
urlpatterns += [
    url(r"^", include("pod.completion.urls")),
]
urlpatterns += [
    url(r"^", include("pod.chapter.urls")),
]
urlpatterns += [
    url(r"^", include("pod.playlist.urls")),
]

if getattr(settings, "USE_PODFILE", False):
    urlpatterns += [
        url(r"^podfile/", include("pod.podfile.urls")),
    ]

for apps in settings.THIRD_PARTY_APPS:
    urlpatterns += [
        url(r"^" + apps + "/", include("pod.%s.urls" % apps)),
    ]

if getattr(settings, "USE_STATS_VIEW", False):
    urlpatterns += [
        url(r"^video_stats_view/$", stats_view, name="video_stats_view"),
        url(
            r"^video_stats_view/(?P<slug>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
        url(
            r"^video_stats_view/(?P<slug>[-\w]+)/(?P<slug_t>[-\w]+)/$",
            stats_view,
            name="video_stats_view",
        ),
    ]

# COMMENT and VOTE
if getattr(settings, "ACTIVE_VIDEO_COMMENT", False):
    urlpatterns += [
        url(
            r"^comment/(?P<video_slug>[\-\d\w]+)/$",
            get_comments,
            name="get_comments",
        ),
        url(
            r"^comment/(?P<comment_id>[\d]+)/(?P<video_slug>[\-\d\w]+)/$",
            get_children_comment,
            name="get_comment",
        ),
        url(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/$",
            add_comment,
            name="add_comment",
        ),
        url(
            r"^comment/add/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            add_comment,
            name="add_child_comment",
        ),
        url(
            r"^comment/del/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            delete_comment,
            name="delete_comment",
        ),
        url(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/$",
            vote_get,
            name="get_votes",
        ),
        url(
            r"^comment/vote/(?P<video_slug>[\-\d\w]+)/(?P<comment_id>[\d]+)/$",
            vote_post,
            name="add_vote",
        ),
    ]

# CHANNELS
urlpatterns += [
    url(r"^", include("pod.video.urls-channels-video")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Change admin site title
admin.site.site_header = _("Pod Administration")
admin.site.site_title = _("Pod Administration")
