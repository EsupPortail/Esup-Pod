"""
Esup-Pod - URL configuration for the authentication app.

This module defines the API endpoints for user authentication, profile management,
and configuration retrieval. It supports multiple authentication methods including
standard JWT, CAS, Shibboleth, and OIDC based on settings.
"""

import django_cas_ng.views
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)

from .conf import auth_settings
from .views import (
    AccessGroupViewSet,
    CASLoginView,
    GroupViewSet,
    LoginView,
    LogoutInfoView,
    OIDCLoginView,
    OwnerViewSet,
    ShibbolethLoginView,
    SiteViewSet,
    UserMeView,
    UserViewSet,
)

router = DefaultRouter()
router.register(r"owners", OwnerViewSet)
router.register(r"users", UserViewSet)
router.register(r"groups", GroupViewSet)
router.register(r"sites", SiteViewSet)
router.register(r"access-groups", AccessGroupViewSet)

urlpatterns = [
    path("users/me/", UserMeView.as_view(), name="user_me"),
    path("", include(router.urls)),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout-info/", LogoutInfoView.as_view(), name="api_logout_info"),
]

if auth_settings.use_local_auth:
    urlpatterns.append(path("token/", LoginView.as_view(), name="token_obtain_pair"))

if auth_settings.use_cas:
    urlpatterns.append(
        path("token/cas/", CASLoginView.as_view(), name="token_obtain_pair_cas")
    )
    urlpatterns.append(
        path(
            "accounts/login",
            django_cas_ng.views.LoginView.as_view(),
            name="cas_ng_login",
        )
    )
    urlpatterns.append(
        path(
            "accounts/logout",
            django_cas_ng.views.LogoutView.as_view(),
            name="cas_ng_logout",
        )
    )

if auth_settings.use_shib:
    urlpatterns.append(
        path(
            "token/shibboleth/",
            ShibbolethLoginView.as_view(),
            name="token_obtain_pair_shibboleth",
        )
    )

if auth_settings.use_oidc:
    urlpatterns.append(
        path("token/oidc/", OIDCLoginView.as_view(), name="token_obtain_pair_oidc")
    )
