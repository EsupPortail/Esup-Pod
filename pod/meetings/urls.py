from django.conf.urls import *
from django.urls import path

from pod.meetings.models import Meetings

from .views import index, add, begin_meeting, delete_meeting

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

app_name = "meetings"

urlpatterns = [
    path('meeting/', index, name='index'),
    path('meeting/add/', add, name='add'),
    url('^meeting/begin/$', begin_meeting, name='begin'),
    url('^meeting/(?P<meeting_id>[a-zA-Z0-9 _-]+)/(?P<password>.*)/delete$', delete_meeting,
        name='delete'),
    path("api/", include(("django_bigbluebutton.api.urls", "django_bigbluebutton.api.urls"), "api_bbb"), ),
]