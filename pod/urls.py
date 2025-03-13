"""Esup-pod URL configuration."""

from django.conf import settings
from django.urls import include
from django.urls import path, re_path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.i18n import JavaScriptCatalog
from django.utils.translation import gettext_lazy as _

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
USE_NOTIFICATIONS = getattr(settings, "USE_NOTIFICATIONS", False)
USE_CUT = getattr(settings, "USE_CUT", False)
USE_MEETING = getattr(settings, "USE_MEETING", False)
USE_XAPI = getattr(settings, "USE_XAPI", False)
USE_OPENCAST_STUDIO = getattr(settings, "USE_OPENCAST_STUDIO", False)
USE_PODFILE = getattr(settings, "USE_PODFILE", False)
USE_PLAYLIST = getattr(settings, "USE_PLAYLIST", False)
USE_DRESSING = getattr(settings, "USE_DRESSING", False)
USE_SPEAKER = getattr(settings, "USE_SPEAKER", False)
USE_IMPORT_VIDEO = getattr(settings, "USE_IMPORT_VIDEO", False)
USE_QUIZ = getattr(settings, "USE_QUIZ", False)
USE_AI_ENHANCEMENT = getattr(settings, "USE_AI_ENHANCEMENT", False)
WEBTV_MODE = getattr(settings, "WEBTV_MODE", False)
USE_DUPLICATE = getattr(settings, "USE_DUPLICATE", False)

if USE_CAS:
    from cas import views as cas_views


urlpatterns = [
    path("select2/", include("django_select2.urls")),
    path("robots.txt", robots_txt),
    path("info_pod.json", info_pod),
    re_path(r"^admin/", admin.site.urls),
    # WYSIWYG editor
    path("tinymce/", include("tinymce.urls")),
    # Translation
    path("i18n/", include("django.conf.urls.i18n")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    # Maintenance mode
    path("maintenance/", maintenance, name="maintenance"),
    # videos
    path("videos/", include("pod.video.urls-videos")),
    path("rss", include("pod.video.urls-rss")),
    path("video/", include("pod.video.urls")),
    re_path(r"^ajax_calls/search_user/", user_autocomplete),
    # my channels
    path("channels/", include("pod.video.urls-channels")),
    # recording
    path("record/", include("pod.recorder.urls")),
    # search
    path("search/", include("pod.video_search.urls")),
    path("authentication_", include("pod.authentication.urls")),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(),
        {"redirect_authenticated_user": True},
        name="local-login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        {"next_page": "/"},
        name="local-logout",
    ),
    path("accounts/change-password/", auth_views.PasswordChangeView.as_view()),
    path("accounts/reset-password/", auth_views.PasswordResetView.as_view()),
    path("accounts/userpicture/", userpicture, name="userpicture"),
    path("accounts/set-notifications/", set_notifications, name="set_notifications"),
    # rest framework
    path("api-auth/", include("rest_framework.urls")),
    path("rest/", include(rest_urlpatterns)),
    # contact_us
    path("contact_us/", contact_us, name="contact_us"),
    path("captcha/", include("captcha.urls")),
    path("download/", download_file, name="download_file"),
    # custom
    path("custom/", include("pod.custom.urls")),
    # pwa
    path("", include("pwa.urls")),
]

# WEBPUSH
if USE_NOTIFICATIONS:
    urlpatterns += [
        # webpush
        path("webpush/", include("webpush.urls")),
    ]

# CAS
if USE_CAS:
    # urlpatterns += [re_path(r'^sso-cas/', include('cas.urls')), ]
    urlpatterns += [
        path("sso-cas/login/", cas_views.login, name="cas-login"),
        path("sso-cas/logout/", cas_views.logout, name="cas-logout"),
    ]

# OIDC
if USE_OIDC:
    urlpatterns += [
        path("oidc/", include("mozilla_django_oidc.urls")),
    ]

# PWA
urlpatterns += [
    path(
        "pwa/", include("pod.progressive_web_app.urls", namespace="progressive_web_app")
    ),
]

if USE_MEETING:
    urlpatterns += [
        path("meeting/", include("pod.meeting.urls")),
    ]

if USE_XAPI:
    urlpatterns += [
        path("xapi/", include("pod.xapi.urls")),
    ]

# RECORDER
if USE_OPENCAST_STUDIO:
    urlpatterns += [
        path("studio/", include("pod.recorder.studio_urls")),
        path("digest/studio/", include("pod.recorder.studio_urls_digest")),
    ]

# PODFILE
if USE_PODFILE:
    urlpatterns += [
        path("podfile/", include("pod.podfile.urls")),
    ]

for apps in settings.THIRD_PARTY_APPS:
    urlpatterns += [
        re_path(r"^" + apps + "/", include("pod.%s.urls" % apps, namespace=apps)),
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
        path("import_video/", include("pod.import_video.urls", namespace="import_video")),
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
    path("", include("pod.video.urls-channels-video")),
]

# Change admin site title
admin.site.site_header = _("Pod Administration")
admin.site.site_title = _("Pod Administration")
