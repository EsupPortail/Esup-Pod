from .views import authentication_login
from .views import authentication_logout
from .views import authentication_login_gateway

from django.urls import re_path

app_name = "authentication"

urlpatterns = [
    # auth cas
    re_path(
        r"^login/$",
        authentication_login,
        name="authentication_login",
    ),
    re_path(
        r"^logout/$",
        authentication_logout,
        name="authentication_logout",
    ),
    # re_path(r"^login/$", authentication_login, name="login"),
    # re_path(r"^logout/$", authentication_logout, name="logout"),
    re_path(
        r"^login_gateway/$",
        authentication_login_gateway,
        name="authentication_login_gateway",
    ),
]
