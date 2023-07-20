"""Useful functions for the entire Pod application."""
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _


def is_ajax(request) -> bool:
    """Check that the request is made by a javascript call."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


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
