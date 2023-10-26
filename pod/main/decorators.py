"""Esup-Pod additionals view decorators."""

from functools import wraps
from django.core.exceptions import PermissionDenied


def ajax_login_required(_view):
    """
    Decorate views to checks that current request is made with ajax AND user is logged.

    If your request wait for a json, it's better than adding ajax_required+login_required
    raise PermissionDenied if necessary (instead of redirecting to login page).
    """

    @wraps(_view)
    def _wrapped_view(request, *args, **kwargs):
        if (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            and request.user.is_authenticated
        ):
            return _view(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    return _wrapped_view


def ajax_required(_view):
    """
    Decorate views to checks that current request is ajax.

    raise PermissionDenied if necessary.
    """

    @wraps(_view)
    def _wrapped_view(request, *args, **kwargs):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return _view(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    return _wrapped_view


def admin_required(_view):
    """
    Check if user must have admin role.

    Decorator for views that checks that the logged in user is a superuser, redirecting
    to the log-in page if necessary.
    """

    @wraps(_view)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return _view(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    return _wrapped_view
