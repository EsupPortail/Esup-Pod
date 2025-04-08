"""Management of webinars for the Meeting module."""

import json
import logging
import requests
import threading
import time

from django.contrib import messages
from django.core.handlers.wsgi import WSGIRequest
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from pod.main.utils import display_message_with_icon
from pod.meeting.models import Meeting, Livestream
from pod.meeting.utils import slash_join

log = logging.getLogger("webinar")


def start_webinar(request: WSGIRequest, meet_id: int) -> None:
    """Start a webinar and send a thread to stop it automatically at the end."""
    try:
        # Get the current meeting
        meeting = Meeting.objects.get(id=meet_id)

        # No thread for start the webinar
        start_webinar_livestream(request.get_host(), meet_id)

        # Thread for stop the webinar
        t_stop = threading.Thread(target=stop_webinar_livestream, args=[meet_id, False])
        t_stop.daemon = True
        t_stop.start()
        display_message_with_icon(
            request,
            messages.INFO,
            _("Webinar mode has been successfully started for “%(name)s” meeting.")
            % ({"name": meeting.name}),
        )
        # Manage enable_chat is False by default
        if meeting.enable_chat is False:
            # Send a toggle request to SIPMediaGW
            toggle_rtmp_gateway(meet_id)
    except Exception as exc:
        log.error(
            "Error to start webinar mode for “%(id)s” meeting: %(exc)s"
            % {"id": meet_id, "exc": str(exc)}
        )
        display_message_with_icon(
            request,
            messages.ERROR,
            _("Error to start webinar mode for “%(name)s” meeting: %(exc)s")
            % {"name": meeting.name, "exc": str(exc)},
        )


def stop_webinar(request: WSGIRequest, meet_id: int) -> None:
    """Stop the webinar."""
    try:
        # Get the current meeting
        meeting = Meeting.objects.get(id=meet_id)

        # No thread for stop the webinar in such a case
        stop_webinar_livestream(meet_id, True)

        display_message_with_icon(
            request,
            messages.INFO,
            _("Webinar mode has been successfully stopped for “%(name)s” meeting.")
            % {"name": meeting.name},
        )
    except Exception as exc:
        log.error(
            "Error to stop webinar mode for “%(id)s” meeting: %(exc)s"
            % {"id": meet_id, "exc": str(exc)}
        )
        display_message_with_icon(
            request,
            messages.ERROR,
            _("Error to stop webinar mode for “%(name)s” meeting: %(exc)s")
            % {"name": meeting.name, "exc": str(exc)},
        )


def start_webinar_livestream(pod_host: str, meet_id: int) -> None:
    """Run the steps to start the webinar livestream."""
    try:
        if pod_host.find("localhost") != -1:
            raise ValueError(
                _(
                    "it is not possible to use a development server "
                    "(localhost) for this functionality."
                )
            )

        # Get the current meeting
        meeting = Meeting.objects.get(id=meet_id)

        # Manage meeting's livestream
        livestream = manage_meeting_livestream(meeting)

        # Start RTMP Gateway for SIPMediaGW
        start_rtmp_gateway(pod_host, meet_id, livestream.id)
    except Exception as exc:
        log.error(
            "Error to start webinar mode for “%s” meeting: %s" % (meet_id, str(exc))
        )
        raise ValueError(str(exc))


def stop_webinar_livestream(meet_id: int, force: bool) -> None:
    """Stop the webinar when meeting is stopped or when user forces to stop it."""
    try:
        log.info("stop_webinar_livestream %s: %s" % (meet_id, "stop"))
        # Get the meeting
        meeting = Meeting.objects.get(id=meet_id)
        # Search for the livestream used for this webinar
        livestream_in_progress = Livestream.objects.filter(
            meeting=meeting, status=1
        ).first()
        # When not forced, wait to meeting's end to stop RTMP gateway
        # After 5h (max duration for a meeting), stop the RTMP gateway
        if not force:
            # Wait for the meeting to end
            wait_meeting_is_stopped(meeting)

        if livestream_in_progress:
            # Stop RTMP Gateway for SIPMediaGW
            stop_rtmp_gateway(meet_id, livestream_in_progress.id)

            # Change livestream status
            livestream_in_progress.status = 2
            livestream_in_progress.save()
        else:
            log.error("No livestream object found for webinar id %s" % meet_id)

    except Exception as exc:
        log.error("Error to stop webinar mode for “%s” meeting: %s" % (meet_id, str(exc)))
        if force:
            raise ValueError(str(exc))


def wait_meeting_is_stopped(meeting: Meeting) -> None:
    """Check regularly if meeting is stopped.

    If meeting is running, wait to make another check (5h max).
    If meeting was stopped, continue without delay.
    """
    # Meeting is stopped?
    is_stopped = False
    # Check timeout if BBB meeting is still running (in seconds)
    delay = 60

    i = 1
    time.sleep(delay)
    while i < int(18000 / delay):
        # Check regularly
        if meeting.get_is_meeting_running() is True:
            is_stopped = False
            log.info(
                "check status for meeting %s “%s”: %s"
                % (meeting.id, meeting.name, "Meeting is running")
            )
            time.sleep(delay)
        else:
            log.info(
                "check status for meeting %s “%s”: %s"
                % (meeting.id, meeting.name, "Meeting is not running")
            )
            # Exit if meeting was stopped during 2 checks
            if is_stopped:
                break
            else:
                time.sleep(delay)
            is_stopped = True
        i += 1


def manage_meeting_livestream(meeting: Meeting):
    """Manage the meeting's livestream."""
    # Search existant livestream for this meeting
    livestream = Livestream.objects.filter(
        meeting=meeting,
    ).first()
    if livestream:
        # Live in progress
        livestream.status = 1
        livestream.save()
    else:
        log.error("No livestream object found for webinar id %s" % meeting.id)
    return livestream


def start_rtmp_gateway(pod_host: str, meet_id: int, livestream_id: int) -> None:
    """Run the start command for SIPMediaGW RTMP gateway."""
    # Get the current meeting
    meeting = Meeting.objects.get(id=meet_id)
    livestream = Livestream.objects.get(id=livestream_id)
    # Base URL; example format: pod.univ.fr/meeting/##id##/##hash/key##
    # with a / before the last 10 characters
    meeting_base_url = slash_join(
        pod_host, "meeting", meeting.meeting_id, meeting.get_hashkey()
    )
    # Room used (last 10 characters)
    room = meeting.get_hashkey()[-10:]
    # Domain (without last 10 characters)
    domain = meeting_base_url[:-10]
    # RTMP stream URL
    rtmp_stream_url = livestream.live_gateway.rtmp_stream_url
    # Start URL on SIPMediaGW server
    sipmediagw_url = slash_join(livestream.live_gateway.sipmediagw_server_url, "start")

    # SIPMediaGW start request
    headers = {
        "Authorization": "Bearer %s" % livestream.live_gateway.sipmediagw_server_token,
    }
    params = {
        "room": room,
        "domain": domain,
        "rtmpDst": rtmp_stream_url,
    }
    response = requests.get(sipmediagw_url, params=params, headers=headers, verify=False)
    # Output in JSON (ex: {"res": "ok", "app": "streaming", "uri": ""})
    json_response = json.loads(response.text)

    log.info(
        "start_rtmp_gateway for meeting %s “%s”: %s"
        % (meeting.id, meeting.name, response.text)
    )

    if json_response["status"] != "success":
        message = json_response["details"]
        raise ValueError(mark_safe(message))


def stop_rtmp_gateway(meet_id: int, livestream_id: int) -> None:
    """Run the stop command for SIPMediaGW RTMP gateway."""
    # Get the current meeting
    meeting = Meeting.objects.get(id=meet_id)
    livestream = Livestream.objects.get(id=livestream_id)
    # Room used (last 10 characters)
    room = meeting.get_hashkey()[-10:]
    # Stop URL on SIPMediaGW server
    sipmediagw_url = slash_join(livestream.live_gateway.sipmediagw_server_url, "stop")

    # SIPMediaGW stop request
    headers = {
        "Authorization": "Bearer %s" % livestream.live_gateway.sipmediagw_server_token,
    }
    params = {
        "room": room,
    }
    response = requests.get(sipmediagw_url, params=params, headers=headers, verify=False)
    # Output in JSON (ex: {"res": "Container gw0 Stopping =>... Container gw0 Removed"})
    json_response = json.loads(response.text)

    log.info(
        "stop_rtmp_gateway for meeting %s “%s”: %s"
        % (meeting.id, meeting.name, response.text)
    )

    if json_response["status"] != "success":
        message = json_response["details"]
        raise ValueError(mark_safe(message))


def toggle_rtmp_gateway(meet_id: int) -> None:
    """Run the toggle (to show chat or not) command for SIPMediaGW RTMP gateway."""
    # Get the current meeting
    meeting = Meeting.objects.get(id=meet_id)
    # Room used (last 10 characters)
    room = meeting.get_hashkey()[-10:]
    # Search for the livestream used for this webinar
    livestream = Livestream.objects.filter(meeting=meeting, status=1).first()
    if livestream:
        # Toogle URL on SIPMediaGW server
        sipmediagw_url = slash_join(livestream.live_gateway.sipmediagw_server_url, "chat")

        # SIPMediaGW toogle request
        headers = {
            "Authorization": "Bearer %s"
            % livestream.live_gateway.sipmediagw_server_token,
        }
        params = {"room": room, "toggle": True}
        response = requests.get(
            sipmediagw_url, params=params, headers=headers, verify=False
        )

        # Specific error message when not started
        message = response.text
        # Output in JSON (ex: {"res": "ok"})
        json_response = json.loads(response.text)
        if json_response["res"] != "ok":
            message = "Toogle was sent before SIPMediaGW start (%s)" % response.text

        log.info(
            "toggle_rtmp_gateway for meeting %s “%s”: %s"
            % (meeting.id, meeting.name, message)
        )
    else:
        log.error("No livestream object found for webinar id %s" % meet_id)


def chat_rtmp_gateway(meet_id: int, msg: str) -> None:
    """Send message command to SIPMediaGW RTMP gateway."""
    # Get the current meeting
    meeting = Meeting.objects.get(id=meet_id)
    # Room used (last 10 characters)
    room = meeting.get_hashkey()[-10:]
    # Search for the livestream used for this webinar
    livestream = Livestream.objects.filter(meeting=meeting, status=1).first()
    if livestream:
        # Toogle URL on SIPMediaGW server
        sipmediagw_url = slash_join(livestream.live_gateway.sipmediagw_server_url, "chat")

        # SIPMediaGW toogle request
        headers = {
            "Content-Type": "application/json",
        }
        # Manage quotes in msg
        msg = msg.replace("'", "’")
        msg = msg.replace('"', "’")
        json_data = {"room": room, "msg": msg}
        response = requests.post(
            sipmediagw_url, headers=headers, json=json_data, verify=False
        )

        message = response.text
        # Output in JSON (ex: {"res": "ok"})
        json_response = json.loads(response.text)

        log.info(
            "chat_rtmp_gateway for meeting %s “%s”: %s"
            % (meeting.id, meeting.name, message)
        )

        if json_response["res"].find("ok") == -1:
            message = json_response["res"]
            raise ValueError(mark_safe(message))
    else:
        log.error("No livestream object found for webinar id %s" % meet_id)
