from django.urls import path, include
from django.conf import settings
import django_cas_ng.views
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    LoginView,
    UserMeView,
    CASLoginView,
    ShibbolethLoginView,
    OIDCLoginView,
    OwnerViewSet,
    UserViewSet,
    GroupViewSet,
    SiteViewSet,
    AccessGroupViewSet,
    LogoutInfoView,
    LoginConfigView
)

router = DefaultRouter()
router.register(r'owners', OwnerViewSet)
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'sites', SiteViewSet)
router.register(r'access-groups', AccessGroupViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('users/me/', UserMeView.as_view(), name='user_me'),
    path('logout-info/', LogoutInfoView.as_view(), name='api_logout_info'),
    path('login-config/', LoginConfigView.as_view(), name='api_login_config'),
]

if settings.USE_LOCAL_AUTH:
    urlpatterns.append(
        path('token/', LoginView.as_view(), name='token_obtain_pair')
    )

if settings.USE_CAS:
    urlpatterns.append(
        path(
            'token/cas/',
            CASLoginView.as_view(),
            name='token_obtain_pair_cas'
        )
    )
    urlpatterns.append(
        path(
            'accounts/login',
            django_cas_ng.views.LoginView.as_view(),
            name='cas_ng_login'
        )
    )
    urlpatterns.append(
        path(
            'accounts/logout',
            django_cas_ng.views.LogoutView.as_view(),
            name='cas_ng_logout'
        )
    )

if settings.USE_SHIB:
    urlpatterns.append(
        path(
            'token/shibboleth/',
            ShibbolethLoginView.as_view(),
            name='token_obtain_pair_shibboleth'
        )
    )

if settings.USE_OIDC:
    urlpatterns.append(
        path(
            'token/oidc/',
            OIDCLoginView.as_view(),
            name='token_obtain_pair_oidc'
        )
    )
