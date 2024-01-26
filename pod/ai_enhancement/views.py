import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

from pod.video.models import Discipline


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
        "disciplines": list(Discipline.objects.all().values_list("title", flat=True)),
    }
    return HttpResponse(json.dumps(data_to_serialize), content_type="application/json")
