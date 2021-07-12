from django.conf.urls import url
from .views import list_meeting, publish_meeting, live_list_meeting
from .views import live_publish_meeting, live_publish_chat

app_name = "bbb"

urlpatterns = [
    url(r"^list_meeting/$", list_meeting, name="list_meeting"),
    url(
        r"^publish_meeting/(?P<id>[\d]+)/$",
        publish_meeting,
        name="publish_meeting",
    ),
    url(r"^live_list_meeting/$", live_list_meeting, name="live_list_meeting"),
    url(
        r"^live_publish_meeting/(?P<id>[\d]+)/$",
        live_publish_meeting,
        name="live_publish_meeting",
    ),
    url(
        r"^live_publish_chat/(?P<id>[\d]+)/$",
        live_publish_chat,
        name="live_publish_chat",
    ),
]
