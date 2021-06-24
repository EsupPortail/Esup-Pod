from functools import wraps

from django.core.exceptions import PermissionDenied


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