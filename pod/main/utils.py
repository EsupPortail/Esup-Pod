"""Useful functions for the entire Pod application."""

import base64
import io
import json

import qrcode

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from webvtt import Caption, WebVTT

from pod import settings
from pod.playlist.utils import get_playlist_list_for_user
from pod.video.models import Video
from pod.video_encode_transcript.encoding_utils import sec_to_timestamp

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)


def is_ajax(request) -> bool:
    """Check that the request is made by a javascript call."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def get_number_video_for_user(user: User) -> int:
    """
    Get the number of videos for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of videos.
    """
    return Video.objects.filter(owner=user).count()


def get_number_playlist_for_user(user: User) -> int:
    """
    Get the number of playlists for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of playlist.
    """
    return get_playlist_list_for_user(user).count()


def display_message_with_icon(request, type, message) -> None:
    """Procedure that allows to display a message with icon to the user.

    Return message with icon, depending on message type.
    Args:
        request (Request): HTTP request
        type (String): message type
        message (String): message without icon
    """
    mapp = {
        messages.ERROR: "exclamation-circle",
        messages.WARNING: "exclamation-triangle",
        messages.SUCCESS: "check-circle",
        messages.INFO: "info-circle",
        messages.DEBUG: "code",
    }
    icon = mapp.get(type, "info-circle")
    msg = "<div class='d-flex'>"
    msg += "  <i aria-hidden='true' class='bi bi-" + icon + " me-2'></i>"
    msg += "  <span class='alert-message'>" + message + "</span>"
    msg += "</div>"
    messages.add_message(request, type, mark_safe(msg))


def dismiss_stored_messages(request) -> None:
    """
    Tweak that dismiss messages (django.contrib.messages) stored.

    to prevent them to pop on reload (asynchronous views)

    Args:
        request (Request): HTTP request
    """
    system_messages = messages.get_messages(request)
    for _msg in system_messages:
        pass


def get_max_code_lvl_messages(request):
    """Get max level of request's stored messages.

    Args:
        request (Request): HTTP request
    """
    max_code_lvl = 0
    system_messages = messages.get_messages(request)
    if len(system_messages) > 0:
        max_code_lvl = max(list(map(lambda x: x.level, system_messages)))
    return max_code_lvl


def secure_post_request(request) -> None:
    """Secure that this request is POST type.

    Args:
        request (Request): HTTP request

    Raises:
        PermissionDenied: if method not POST
    """
    if request.method != "POST":
        display_message_with_icon(
            request, messages.WARNING, _("This view cannot be accessed directly.")
        )
        raise PermissionDenied


def generate_qrcode(url: str, alt: str, request=None):
    """
    Generate qrcode for live event or video share link.

    Args:
        url (string): Url corresponding to link
        id (number): Identifier of object
        alt (string): Translated string for alternative text
        request (Request): HTTP Request

    Returns:
        string: HTML-formed qrcode

    """
    url_scheme = "https" if SECURE_SSL_REDIRECT else "http"
    data = "".join(
        [
            url_scheme,
            "://",
            get_current_site(request).domain,
            url,
        ]
    )
    img = qrcode.make(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return mark_safe(
        f'<img id="qrcode" src="data:image/png;base64, {img_str}" '
        + f'width="200px" height="200px" alt="{alt}">'
    )


def extract_json_from_str(content_to_extract: str) -> dict:
    """Extract the JSON from a string."""
    start_index = content_to_extract.find("{")
    end_index = content_to_extract.rfind("}")
    json_string = content_to_extract[start_index : end_index + 1]
    try:
        return json.loads(json_string)
    except json.JSONDecodeError:
        return {"error": "JSONDecodeError: The string is not a valid JSON string."}


def json_to_web_vtt(json_data: dict, duration: int) -> WebVTT:
    """Convert the JSON to WebVTT."""
    web_vtt = WebVTT()
    for caption in json_data:
        if caption["start"] >= duration:
            break
        # identifier = f"{caption['start']}-{caption['end']}"
        start = sec_to_timestamp(caption["start"])
        end = sec_to_timestamp(caption["end"] if caption["end"] < duration else duration)
        caption = Caption(start=start, end=end, text=caption["text"])
        web_vtt.captions.append(caption)
    return web_vtt


def sizeof_fmt(num: float, suffix: str = "B") -> str:
    """Humanize size of a file."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def remove_trailing_spaces(text: str) -> str:
    """Remove trailing spaces in a multi-line string."""
    lines = text.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.rstrip()
        if line != "":
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)
