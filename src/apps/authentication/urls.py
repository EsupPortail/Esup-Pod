from django.urls import path
from django.conf import settings
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import LoginView, UserMeView, CASLoginView

urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('users/me/', UserMeView.as_view(), name='user_me'),
]

if settings.USE_LOCAL_AUTH:
    urlpatterns.append(
        path('token/', LoginView.as_view(), name='token_obtain_pair')
    )

if settings.USE_CAS:
    urlpatterns.append(
        path('token/cas/', CASLoginView.as_view(), name='token_obtain_pair_cas')
    )