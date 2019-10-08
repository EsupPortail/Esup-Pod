from django.conf.urls import url

from . import views

app_name = "custom"

urlpatterns = [
    url(r'^$', views.index, name="home"),
]
