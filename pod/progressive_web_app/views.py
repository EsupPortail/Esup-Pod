"""Esup-Pod progressive Web App views."""

from django.shortcuts import render
from .utils import notify_user
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied


def debug(request):
    """Debug page for simple push notification."""
    if not request.user.is_superuser:
        raise PermissionDenied()

    return render(
        request,
        "debug.html",
    )


def send(request):
    """Send a 'hello world' push notification for debug purpose."""
    if not request.user.is_superuser:
        raise PermissionDenied()

    notify_user(request.user, "Hello", "World!")
    return JsonResponse({"success": True})
