from .views import authentication_login
from .views import authentication_logout
from .views import authentication_login_gateway

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
    # re_path(r"^login/$", authentication_login, name="login"),
    # re_path(r"^logout/$", authentication_logout, name="logout"),
    path(
        "login_gateway/",
        authentication_login_gateway,
        name="authentication_login_gateway",
    ),
]
