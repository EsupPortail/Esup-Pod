from functools import wraps
from urllib.parse import urlparse

from django.core.exceptions import PermissionDenied
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url
from django.conf import settings


def admin_passes_test(
    test_func=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """
    def decorator(_view):
        @wraps(_view)
        def _wrapped_view(request, *args, **kwargs):
            if test_func is not None:
                return _view(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()

            if not request.user.is_authenticated:
                return redirect_to_login(
                    path, resolved_login_url, redirect_field_name)
            elif not request.user.is_superuser:
                raise PermissionDenied()
            else:
                return _view(request, *args, **kwargs)

        return _wrapped_view
    return decorator


def ajax_required(_view):
    """
    Decorator for views that checks that current request is ajax, raise
    PermissionDenied if necessary.
    """
    @wraps(_view)
    def _wrapped_view(request, *args, **kwargs):

        if request.is_ajax():
            return _view(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    return _wrapped_view


def admin_required(
    function=None,
    redirect_field_name=REDIRECT_FIELD_NAME,
    login_url=None
):
    """
    Decorator for views that checks that the logged in user is a superuser, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = admin_passes_test(
        None,
        redirect_field_name=redirect_field_name,
        login_url=login_url
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
