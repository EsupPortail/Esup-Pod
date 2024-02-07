import json

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from pod.ai_enhancement.models import AIEnrichment
from pod.ai_enhancement.utils import AristoteAI, enrichment_is_already_asked
from pod.video.models import Discipline, Video

AI_ENRICHMENT_CLIENT_ID = getattr(settings, "AI_ENRICHMENT_CLIENT_ID", "mocked_id")
AI_ENRICHMENT_CLIENT_SECRET = getattr(settings, "AI_ENRICHMENT_CLIENT_SECRET", "mocked_secret")


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


def send_enrichment_creation_request(request: WSGIRequest):
    """Send a request to create an enrichment."""
    aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
    # aristote.create_enrichment_from_url() # TODO add the parameters
    # data_to_serialize = {
    #     "method": request.method,
    #     "GET": dict(request.GET),
    #     "POST": dict(request.POST),
    #     "files": request.FILES,
    #     "headers": dict(request.headers),
    #     "path": request.path,
    #     "query_params": request.GET,
    # }
    data_to_serialize = {
        "message": "Not implemented yet",
    }
    # TODO Finish this
    return HttpResponse(json.dumps(data_to_serialize), content_type="application/json")


def enrich_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    video = get_object_or_404(Video, slug=video_slug)
    if enrichment_is_already_asked(video):
        enrichment = AIEnrichment.objects.filter(video=video).first()
        aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
        latest_version = aristote.get_latest_enrichment_version(enrichment.ai_enrichment_id_in_aristote)
        if latest_version["status"] != "KO":
            return HttpResponse(json.dumps(latest_version), content_type="application/json")
        else:
            return HttpResponse("Enrichment already asked. Wait please.", status=200)   # TODO: change this line
    else:
        return HttpResponse(
            "Enrichment has been created. Please wait. You will receive an email when Aristote will finish that.",
            status=200,
        )  # TODO: change this lines

