from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME


def ajax_required(_view):
    @wraps(_view)
    def _wrapped_view(request, *args, **kwargs):

        if request.is_ajax():
            return _view(request, *args, **kwargs)
        else:
            raise PermissionDenied()

    return _wrapped_view


def admin_required(
    function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the logged in user is a superuser, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
