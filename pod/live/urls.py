from django.urls import path, re_path

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
    path(
        "ajax_calls/event_startrecord/",
        ajax_event_startrecord,
        name="ajax_event_startrecord",
    ),
    path(
        "ajax_calls/event_stoprecord/",
        ajax_event_stoprecord,
        name="ajax_event_stoprecord",
    ),
    path(
        "ajax_calls/event_splitrecord/",
        ajax_event_splitrecord,
        name="ajax_event_splitrecord",
    ),
    path(
        "ajax_calls/event_start_streaming/",
        ajax_event_start_streaming,
        name="ajax_event_start_streaming",
    ),
    path(
        "ajax_calls/event_stop_streaming/",
        ajax_event_stop_streaming,
        name="ajax_event_stop_streaming",
    ),
    path(
        "ajax_calls/event_get_rtmp_config/",
        ajax_event_get_rtmp_config,
        name="ajax_event_get_rtmp_config",
    ),
    path(
        "ajax_calls/getbroadcastersfrombuiding/",
        broadcasters_from_building,
        name="broadcasters_from_building",
    ),
    path(
        "ajax_calls/getbroadcasterrestriction/",
        broadcaster_restriction,
        name="ajax_broadcaster_restriction",
    ),
    path(
        "ajax_calls/geteventinforcurrentecord/",
        ajax_event_info_record,
        name="ajax_event_info_record",
    ),
    path(
        "ajax_calls/geteventvideocards/",
        event_get_video_cards,
        name="event_get_video_cards",
    ),
    path(
        "ajax_calls/isstreamavailabletorecord/",
        ajax_is_stream_available_to_record,
        name="ajax_is_stream_available_to_record",
    ),
    path(
        "ajax_calls/getmandatoryparameters/",
        ajax_get_mandatory_parameters,
        name="ajax_get_mandatory_parameters",
    ),
    re_path(r"^ajax_calls/heartbeat/", heartbeat, name="heartbeat"),
    re_path(r"^direct/(?P<slug>[\-\w]+)/$", direct, name="direct"),
    path("directs/", directs_all, name="directs_all"),
    path("directs/<int:building_id>/", directs, name="directs"),
    re_path(r"^event/(?P<slug>[\-\w]+)/$", event, name="event"),
    re_path(
        r"^event/(?P<slug>[\-\w]+)/(?P<slug_private>[\-\w]+)/$",
        event,
        name="event_private",
    ),
    path("event_edit/", event_edit, name="event_edit"),
    re_path(r"^event_edit/(?P<slug>[\-\w]+)/$", event_edit, name="event_edit"),
    re_path(r"^event_delete/(?P<slug>[\-\w]+)/$", event_delete, name="event_delete"),
    path("events/", events, name="events"),
    path("my_events/", my_events, name="my_events"),
    path(
        "event_immediate_edit/<int:broadcaster_id>/",
        event_immediate_edit,
        name="event_immediate_edit",
    ),
]
