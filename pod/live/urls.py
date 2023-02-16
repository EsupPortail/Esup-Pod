from django.conf.urls import url

from .views import (
    broadcasters_from_building,
    event,
    events,
    event_edit,
    event_delete,
    heartbeat,
    my_events,
    direct,
    directs,
    directs_all,
    ajax_event_startrecord,
    ajax_event_stoprecord,
    ajax_event_splitrecord,
    event_isstreamavailabletorecord,
    event_video_transform,
    event_get_video_cards,
    ajax_event_info_record,
    broadcaster_restriction,
)

app_name = "live"

urlpatterns = []

urlpatterns += [
    # url(r"^$", lives, name="lives"),
    url(
        r"^ajax_calls/event_startrecord/$",
        ajax_event_startrecord,
        name="ajax_event_startrecord",
    ),
    url(
        r"^ajax_calls/event_stoprecord/$",
        ajax_event_stoprecord,
        name="ajax_event_stoprecord",
    ),
    url(
        r"^ajax_calls/event_splitrecord/$",
        ajax_event_splitrecord,
        name="ajax_event_splitrecord",
    ),
    url(
        r"^ajax_calls/getbroadcastersfrombuiding/$",
        broadcasters_from_building,
        name="broadcasters_from_building",
    ),
    url(
        r"^ajax_calls/getbroadcasterrestriction/$",
        broadcaster_restriction,
        name="ajax_broadcaster_restriction",
    ),
    url(
        r"^ajax_calls/geteventinforcurrentecord/$",
        ajax_event_info_record,
        name="ajax_event_info_record",
    ),
    url(
        r"^ajax_calls/geteventvideocards/$",
        event_get_video_cards,
        name="event_get_video_cards",
    ),
    url(r"^ajax_calls/heartbeat/", heartbeat),
    url(r"^direct/(?P<slug>[\-\d\w]+)/$", direct, name="direct"),
    url(r"^directs/$", directs_all, name="directs_all"),
    url(r"^directs/(?P<building_id>[\d]+)/$", directs, name="directs"),
    url(r"^event/(?P<slug>[\-\d\w]+)/$", event, name="event"),
    url(
        r"^event/(?P<slug>[\-\d\w]+)/(?P<slug_private>[\-\d\w]+)/$",
        event,
        name="event_private",
    ),
    url(r"^event_edit/$", event_edit, name="event_edit"),
    url(r"^event_edit/(?P<slug>[\-\d\w]+)/$", event_edit, name="event_edit"),
    url(r"^event_delete/(?P<slug>[\-\d\w]+)/$", event_delete, name="event_delete"),
    url(
        r"^event_isstreamavailabletorecord/$",
        event_isstreamavailabletorecord,
        name="event_isstreamavailabletorecord",
    ),
    url(
        r"^event_video_transform/$",
        event_video_transform,
        name="event_video_transform",
    ),
    url(r"^events/$", events, name="events"),
    url(r"^my_events/$", my_events, name="my_events"),
]
