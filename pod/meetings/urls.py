from django.conf.urls import *
from django.urls import path

from pod.meetings.models import Meetings

from .views import index, add

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    path('meeting/', index, name='index'),
    path('meeting/add/', add, name='add'),
]