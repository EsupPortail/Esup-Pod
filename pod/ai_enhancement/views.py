import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse


def receive_webhook(request: WSGIRequest):
    """Receive webhook from the AI Enhancement service."""
    data_to_serialize = {
        "method": request.method,
        "GET": dict(request.GET),
        "POST": dict(request.POST),
        "files": request.FILES,
        "headers": dict(request.headers),
        "path": request.path,
        "query_params": request.GET,
    }
    return HttpResponse(json.dumps(data_to_serialize), content_type="application/json")
