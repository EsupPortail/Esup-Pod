from django.conf.urls import url
from .views import list_meeting
from .views import publish_meeting

app_name = "bbb"

urlpatterns = [
    url(r'^list_meeting/$', list_meeting, name='list_meeting'),
    url(r'^publish_meeting/(?P<id>[\d]+)/$', publish_meeting,
        name='publish_meeting'),
]
