from django.urls import re_path

from .pilotingInterface import ajax_get_mandatory_parameters
from .views import (
    ajax_event_info_record,
    ajax_event_startrecord,
    ajax_event_stoprecord,
    ajax_event_splitrecord,
    ajax_event_start_streaming,
    ajax_event_stop_streaming,
    ajax_is_stream_available_to_record,
    ajax_event_get_rtmp_config,
    broadcaster_restriction,
    broadcasters_from_building,
    direct,
    directs,
    directs_all,
    event,
    event_delete,
    event_edit,
    event_get_video_cards,
    event_immediate_edit,
    events,
    heartbeat,
    my_events,
)

app_name = "live"

urlpatterns = []

urlpatterns += [
    # re_path(r"^$", lives, name="lives"),
    re_path(
        r"^ajax_calls/event_startrecord/$",
        ajax_event_startrecord,
        name="ajax_event_startrecord",
    ),
    re_path(
        r"^ajax_calls/event_stoprecord/$",
        ajax_event_stoprecord,
        name="ajax_event_stoprecord",
    ),
    re_path(
        r"^ajax_calls/event_splitrecord/$",
        ajax_event_splitrecord,
        name="ajax_event_splitrecord",
    ),
    re_path(
        r"^ajax_calls/event_start_streaming/$",
        ajax_event_start_streaming,
        name="ajax_event_start_streaming",
    ),
    re_path(
        r"^ajax_calls/event_stop_streaming/$",
        ajax_event_stop_streaming,
        name="ajax_event_stop_streaming",
    ),
    re_path(
        r"^ajax_calls/event_get_rtmp_config/$",
        ajax_event_get_rtmp_config,
        name="ajax_event_get_rtmp_config",
    ),
    re_path(
        r"^ajax_calls/getbroadcastersfrombuiding/$",
        broadcasters_from_building,
        name="broadcasters_from_building",
    ),
    re_path(
        r"^ajax_calls/getbroadcasterrestriction/$",
        broadcaster_restriction,
        name="ajax_broadcaster_restriction",
    ),
    re_path(
        r"^ajax_calls/geteventinforcurrentecord/$",
        ajax_event_info_record,
        name="ajax_event_info_record",
    ),
    re_path(
        r"^ajax_calls/geteventvideocards/$",
        event_get_video_cards,
        name="event_get_video_cards",
    ),
    re_path(
        r"^ajax_calls/isstreamavailabletorecord/$",
        ajax_is_stream_available_to_record,
        name="ajax_is_stream_available_to_record",
    ),
    re_path(
        r"^ajax_calls/getmandatoryparameters/$",
        ajax_get_mandatory_parameters,
        name="ajax_get_mandatory_parameters",
    ),
    re_path(r"^ajax_calls/heartbeat/", heartbeat, name="heartbeat"),
    re_path(r"^direct/(?P<slug>[\-\w]+)/$", direct, name="direct"),
    re_path(r"^directs/$", directs_all, name="directs_all"),
    re_path(r"^directs/(?P<building_id>\d+)/$", directs, name="directs"),
    re_path(r"^event/(?P<slug>[\-\w]+)/$", event, name="event"),
    re_path(
        r"^event/(?P<slug>[\-\w]+)/(?P<slug_private>[\-\w]+)/$",
        event,
        name="event_private",
    ),
    re_path(r"^event_edit/$", event_edit, name="event_edit"),
    re_path(r"^event_edit/(?P<slug>[\-\w]+)/$", event_edit, name="event_edit"),
    re_path(r"^event_delete/(?P<slug>[\-\w]+)/$", event_delete, name="event_delete"),
    re_path(r"^events/$", events, name="events"),
    re_path(r"^my_events/$", my_events, name="my_events"),
    re_path(
        r"^event_immediate_edit/(?P<broadcaster_id>\d+)/$",
        event_immediate_edit,
        name="event_immediate_edit",
    ),
]
