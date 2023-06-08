"""Useful functions for the entire Pod application."""
from django.contrib import messages
from django.utils.html import mark_safe


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
        messages.ERROR: 'exclamation-circle',
        messages.WARNING: 'exclamation-triangle',
        messages.SUCCESS: 'check-circle',
        messages.INFO: 'info-circle',
        messages.DEBUG: 'code'
    }
    icon = mapp.get(type, 'info-circle')
    msg = "<div class='icon'><i class='bi bi-" + icon + "'></i></div>"
    msg += message
    messages.add_message(request, type, mark_safe(msg))
