from django.urls import path, include
from django.conf import settings
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
    LogoutInfoView
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
]

if getattr(settings, 'USE_LOCAL_AUTH', True):
    urlpatterns.append(
        path('token/', LoginView.as_view(), name='token_obtain_pair')
    )

if getattr(settings, 'USE_CAS', False):
    urlpatterns.append(
        path('token/cas/', CASLoginView.as_view(), name='token_obtain_pair_cas')
    )

if getattr(settings, 'USE_SHIB', False):
    urlpatterns.append(
        path('token/shibboleth/', ShibbolethLoginView.as_view(), name='token_obtain_pair_shibboleth')
    )

if getattr(settings, 'USE_OIDC', False):
    urlpatterns.append(
        path('token/oidc/', OIDCLoginView.as_view(), name='token_obtain_pair_oidc')
    )