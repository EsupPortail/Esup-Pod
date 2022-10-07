from .views import authentication_login
from .views import authentication_logout
from .views import authentication_login_gateway

from django.conf.urls import url

app_name = "authentication"

urlpatterns = [
    # auth cas
    url(
        r"^login/$",
        authentication_login,
        name="authentication_login",
    ),
    url(
        r"^logout/$",
        authentication_logout,
        name="authentication_logout",
    ),
    # url(r"^login/$", authentication_login, name="login"),
    # url(r"^logout/$", authentication_logout, name="logout"),
    url(
        r"^login_gateway/$",
        authentication_login_gateway,
        name="authentication_login_gateway",
    ),
]
