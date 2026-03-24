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

from config.router import router
from src.apps.authentication.conf import auth_settings

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Redirection to Swagger
    path("", RedirectView.as_view(url="api/docs/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/info/", include("src.apps.info.urls")),
    path("api/auth/", include("src.apps.authentication.urls")),
    path("api/encoding/", include("src.apps.encoding.urls")),
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
