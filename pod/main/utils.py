"""Useful functions for the entire Pod application."""

import base64
import io
import qrcode

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _

from pod import settings
from pod.playlist.utils import get_playlist_list_for_user
from pod.video.models import Video

SECURE_SSL_REDIRECT = getattr(settings, "SECURE_SSL_REDIRECT", False)


def is_ajax(request) -> bool:
    """Check that the request is made by a javascript call."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def get_number_video_for_user(user: User) -> int():
    """
    Get the number of videos for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of videos.
    """
    return Video.objects.filter(owner=user).count()


def get_number_playlist_for_user(user: User) -> int():
    """
    Get the number of playlists for a user.

    Args:
        user (:class:`django.contrib.auth.models.User`): The user object

    Returns:
        int: The number of playlist.
    """
    return get_playlist_list_for_user(user).count()


def display_message_with_icon(request, type, message):
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
    msg = "<div class='icon'><i class='bi bi-" + icon + "'></i></div>"
    msg += message
    messages.add_message(request, type, mark_safe(msg))


def dismiss_stored_messages(request):
    """
    Tweak that dismiss messages (django.contrib.messages) stored.

    to prevent them to pop on reload (asynchronous views)

    Args:
        request (Request): HTTP request
    """
    system_messages = messages.get_messages(request)
    for msg in system_messages:
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


def secure_post_request(request):
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


def generate_qrcode(url: str, id: int, alt: str, request=None):
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
    url_immediate_event = reverse(url, args={id})
    data = "".join(
        [
            url_scheme,
            "://",
            get_current_site(request).domain,
            url_immediate_event,
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
