from django.urls import path
from . import views

app_name = "progressive_web_app"


urlpatterns = [
    path("", views.debug, name="debug"),
    path("send", views.send, name="send"),
]
