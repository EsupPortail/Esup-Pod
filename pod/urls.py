"""Esup-pod URL configuration."""

from django.conf import settings
from django.conf.urls import url
from django.conf.urls import include
from django.urls import path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
from django.utils.translation import ugettext_lazy as _

import importlib.util

from pod.main.views import (
    contact_us,
    download_file,
    user_autocomplete,
    maintenance,
    robots_txt,
    info_pod,
    userpicture,
    set_notifications,
)
from pod.main.rest_router import urlpatterns as rest_urlpatterns

USE_CAS = getattr(settings, "USE_CAS", False)
USE_SHIB = getattr(settings, "USE_SHIB", False)
USE_OIDC = getattr(settings, "USE_OIDC", False)
USE_NOTIFICATIONS = getattr(settings, "USE_NOTIFICATIONS", True)
USE_CUT = getattr(settings, "USE_CUT", True)
USE_MEETING = getattr(settings, "USE_MEETING", False)
USE_XAPI = getattr(settings, "USE_XAPI", False)
USE_OPENCAST_STUDIO = getattr(settings, "USE_OPENCAST_STUDIO", False)
USE_PODFILE = getattr(settings, "USE_PODFILE", False)
USE_PLAYLIST = getattr(settings, "USE_PLAYLIST", True)
USE_DRESSING = getattr(settings, "USE_DRESSING", True)
USE_SPEAKER = getattr(settings, "USE_SPEAKER", False)
USE_IMPORT_VIDEO = getattr(settings, "USE_IMPORT_VIDEO", True)
USE_QUIZ = getattr(settings, "USE_QUIZ", True)
USE_AI_ENHANCEMENT = getattr(settings, "USE_AI_ENHANCEMENT", False)
WEBTV_MODE = getattr(settings, "WEBTV_MODE", False)
USE_DUPLICATE = getattr(settings, "USE_DUPLICATE", False)

if USE_CAS:
    from cas import views as cas_views


urlpatterns = [
    url("select2/", include("django_select2.urls")),
    url("robots.txt", robots_txt),
    url("info_pod.json", info_pod),
    url(r"^admin/", admin.site.urls),
    # Translation
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^jsi18n/$", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # Maintenance mode
    url(r"^maintenance/$", maintenance, name="maintenance"),
    # videos
    url(r"^videos/", include("pod.video.urls-videos")),
    url(r"^rss", include("pod.video.urls-rss")),
    url(r"^video/", include("pod.video.urls")),
    url(r"^ajax_calls/search_user/", user_autocomplete),
    # my channels
    url(r"^channels/", include("pod.video.urls-channels")),
    # recording
    url(r"^record/", include("pod.recorder.urls")),
    # search
    url(r"^search/", include("pod.video_search.urls")),
    url(r"^authentication_", include("pod.authentication.urls")),
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
    url(r"^accounts/set-notifications/$", set_notifications, name="set_notifications"),
    # rest framework
    url(r"^api-auth/", include("rest_framework.urls")),
    url(r"^rest/", include(rest_urlpatterns)),
    # contact_us
    url(r"^contact_us/$", contact_us, name="contact_us"),
    url(r"^captcha/", include("captcha.urls")),
    url(r"^download/$", download_file, name="download_file"),
    # custom
    url(r"^custom/", include("pod.custom.urls")),
    # pwa
    url("", include("pwa.urls")),
]

# WEBPUSH
if USE_NOTIFICATIONS:
    urlpatterns += [
        # webpush
        url(r"^webpush/", include("webpush.urls")),
    ]

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

# PWA
urlpatterns += [
    path(
        "pwa/", include("pod.progressive_web_app.urls", namespace="progressive_web_app")
    ),
]

if USE_MEETING:
    urlpatterns += [
        url(r"^meeting/", include("pod.meeting.urls")),
    ]

if USE_XAPI:
    urlpatterns += [
        url(r"^xapi/", include("pod.xapi.urls")),
    ]

# RECORDER
if USE_OPENCAST_STUDIO:
    urlpatterns += [
        url(r"^studio/", include("pod.recorder.studio_urls")),
        url(r"^digest/studio/", include("pod.recorder.studio_urls_digest")),
    ]

# PODFILE
if USE_PODFILE:
    urlpatterns += [
        url(r"^podfile/", include("pod.podfile.urls")),
    ]

for apps in settings.THIRD_PARTY_APPS:
    urlpatterns += [
        url(r"^" + apps + "/", include("pod.%s.urls" % apps, namespace=apps)),
    ]

# CUT
if USE_CUT:
    urlpatterns += [
        path("cut/", include("pod.cut.urls", namespace="cut")),
    ]

# PLAYLIST
if USE_PLAYLIST:
    urlpatterns += [
        path("playlist/", include("pod.playlist.urls", namespace="playlist")),
    ]

# AI ENHANCEMENT
if USE_AI_ENHANCEMENT:
    urlpatterns += [
        path(
            "ai-enhancement/",
            include("pod.ai_enhancement.urls", namespace="ai_enhancement"),
        ),
    ]

# QUIZ
if USE_QUIZ:
    urlpatterns += [
        path("quiz/", include("pod.quiz.urls", namespace="quiz")),
    ]

# DRESSING
if USE_DRESSING:
    urlpatterns += [
        path("dressing/", include("pod.dressing.urls", namespace="dressing")),
    ]

# SPEAKER
if USE_SPEAKER:
    urlpatterns += [
        path("speaker/", include("pod.speaker.urls", namespace="speaker")),
    ]

# IMPORT_VIDEO
if USE_IMPORT_VIDEO:
    urlpatterns += [
        url(
            r"^import_video/", include("pod.import_video.urls", namespace="import_video")
        ),
    ]

if USE_DUPLICATE:
    urlpatterns += [
        path("duplicate/", include("pod.duplicate.urls", namespace="duplicate")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if importlib.util.find_spec("debug_toolbar") is not None:
        urlpatterns += [
            path("__debug__/", include("debug_toolbar.urls")),
        ]

# CHANNELS
urlpatterns += [
    url(r"^", include("pod.video.urls-channels-video")),
]

# Change admin site title
admin.site.site_header = _("Pod Administration")
admin.site.site_title = _("Pod Administration")
