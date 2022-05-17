from django.conf.urls import *
from django.urls import path

from pod.meetings.models import Meetings

from .views import edit_meeting, meeting, create, delete_meeting, join_meeting

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    path('meeting/', meeting, name='meeting'),
    path('meeting/add/', create, name='create'),
    path('meeting/edit/<str:meetingID>', edit_meeting,
        name='edit'),
    path('meeting/delete/<str:meetingID>', delete_meeting,
        name='delete'),
    path('meeting/<str:meetingID>', join_meeting,
        name='join'),
    path('meeting/<str:meetingID>/<str:slug_private>', join_meeting,
        name='join'),
]