from .views import authentication_login
from .views import authentication_logout

from django.urls import path

app_name = "authentication"

urlpatterns = [
    # auth cas
    path(
        "login/",
        authentication_login,
        name="authentication_login",
    ),
    path(
        "logout/",
        authentication_logout,
        name="authentication_logout",
    ),
]
