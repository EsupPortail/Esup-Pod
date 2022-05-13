from django.conf.urls import *
from django.urls import path

from pod.meetings.models import Meetings

from .views import meeting, create, delete_meeting, join_meeting

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    path('meeting/', meeting, name='meeting'),
    path('meeting/add/', create, name='create'),
    #url(r'^meeting/edit/(?P<meeting_id>[a-zA-Z0-9 _-]+)$', edit_meeting,
    #    name='edit'),
    url(r'^meeting/delete/(?P<meetingID>[a-zA-Z0-9 _-]+)$', delete_meeting,
        name='delete'),
    url(r'^meeting/(?P<meetingID>[a-zA-Z0-9 _-]+)$', join_meeting,
        name='join'),
    url(r'^meeting/(?P<meetingID>[a-zA-Z0-9 _-]+)/(?P<slug_private>[\-\d\w]+)/$', join_meeting,
        name='join'),
]