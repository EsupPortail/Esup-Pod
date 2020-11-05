from functools import wraps
from django.core.exceptions import PermissionDenied


def ajax_required(fct):
    @wraps(fct)
    def _wrapped_view(request, *args, **kwargs):
        if request.is_ajax():
            return fct(request, *args, **kwargs)
        else:
            raise PermissionDenied()
        return _wrapped_view
