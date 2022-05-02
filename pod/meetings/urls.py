from django.conf.urls import *

from .views import index, add

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    url(r"^meeting/", index, name="index"),
    url(r"^meeting/add/$", add, name="add"),
]