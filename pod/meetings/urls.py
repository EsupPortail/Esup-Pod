from django.conf.urls import *
from django.urls import path
from django.urls import re_path

from pod.meetings.models import Meetings

from .views import create_meeting, edit_meeting, meeting, delete_meeting, join_meeting

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    re_path(r'^$', meeting, name='meeting'),
    path('add/', create_meeting, name='create'),
    path('edit/<str:meetingID>/', edit_meeting,
        name='edit'),
    path('delete/<str:meetingID>/', delete_meeting,
        name='delete'),
    path('<str:meetingID>/', join_meeting,
        name='join'),
    path('<str:meetingID>/<str:slug_private>/', join_meeting,
        name='join'),
]