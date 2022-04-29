from django.conf.urls import url

from .views import (
    settings,
    broadcasters_from_building,
    building,
    event,
    events,
    event_edit,
    event_delete,
    heartbeat,
    lives,
    my_events,
    video_live,
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

USE_EVENT = getattr(settings, "USE_EVENT", False)

urlpatterns = []

if USE_EVENT:
    urlpatterns += [
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
            r"^ajax_calls/geteventvideocards/$",
            event_get_video_cards,
            name="event_get_video_cards",
        ),
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
            r"^ajax_calls/geteventinforcurrentecord/$",
            ajax_event_info_record,
            name="ajax_event_info_record",
        ),
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

urlpatterns += [
    url(r"^ajax_calls/heartbeat/", heartbeat),
    url(r"^$", lives, name="lives"),
    url(r"^building/(?P<building_id>[\d]+)/$", building, name="building"),
    url(r"^(?P<slug>[\-\d\w]+)/$", video_live, name="video_live"),
]
