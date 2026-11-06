"""
Esup-Pod - Main URL configuration.

Defines the root routing for the project, including Admin, API endpoints,
and Swagger/Redoc documentation. Dynamically configures authentication routes
(CAS vs. standard login) based on AuthConfig.
"""

import django_cas_ng.views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from src.apps.authentication.conf import auth_settings
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Redirection to Swagger
    path("", RedirectView.as_view(url="api/docs/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("src.apps.video.urls")),
    path("api/", include("src.apps.import_video.urls")),
    path("api/info/", include("src.apps.info.urls")),
    path("api/auth/", include("src.apps.authentication.urls")),
    path("api/encoding/", include("src.apps.encoding.urls")),
    path("api/dressing/", include("src.apps.dressing.urls")),
    # NOTE: V4 Compatibility
    # In V4, encoded MP4 files were served directly by Nginx at paths like:
    #   /media/videos/<sha1_owner_hash>/<id_padded>/<id_padded>_<res>.mp4
    # Django never handled those download requests, they went straight to Nginx.
    # To redirect old V4 media links in V5, configure Nginx rewrites instead:
    #
    #   location ~ ^/media/videos/[^/]+/(\d{4})/\1_(\d+)\.mp4$ {
    #       return 301 /api/videos/$1/stream/?resolution=$2;
    #   }
    path("api/", include("src.apps.completion.urls")),
    path("api/collections/", include("src.apps.collection.urls")),
    path("api/layout/", include("src.apps.layout.urls")),
    # SWAGGER
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

if auth_settings.use_cas:
    urlpatterns += [
        path(
            "accounts/login",
            django_cas_ng.views.LoginView.as_view(),
            name="cas_ng_login",
        ),
        path(
            "accounts/logout",
            django_cas_ng.views.LogoutView.as_view(),
            name="cas_ng_logout",
        ),
    ]
else:
    urlpatterns += [
        path(
            "accounts/login",
            auth_views.LoginView.as_view(template_name="admin/login.html"),
            name="cas_ng_login",
        ),
        path("accounts/logout", auth_views.LogoutView.as_view(), name="cas_ng_logout"),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug Toolbar and Silk
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
            path("silk/", include("silk.urls", namespace="silk")),
        ]
