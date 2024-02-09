import json

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect

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


def send_enrichment_creation_request(request: WSGIRequest, aristote: AristoteAI, video: Video) -> HttpResponse:
    """Send a request to create an enrichment."""
    creation_response = aristote.create_enrichment_from_url(
        "https://pod.univ-lille.fr/media/videos/585da9d28e5b53c539a1da3ad0d3a3c294a85b5941e9ce46a40b2e006fa69189/35596/360p.mp4",
        # TODO change this
        ["video/mp4"],
        request.user.username,
        "https://webhook.site/30e3559f-67f6-4078-b4d4-51a357d63354",  # TODO change this
    )
    if creation_response["status"] == "OK":
        AIEnrichment.objects.create(
            video=video,
            ai_enrichment_id_in_aristote=creation_response["id"],
        )
        return HttpResponse(
            "Enrichment has been created. Please wait. You will receive an email when Aristote is finished.",
            status=200,
        )
    else:
        print("Error: ", creation_response["status"])   # TODO create a real error
    return redirect("video:video", slug=video.slug)


def enrich_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
    if enrichment_is_already_asked(video):
        enrichment = AIEnrichment.objects.filter(video=video).first()
        latest_version = aristote.get_latest_enrichment_version(enrichment.ai_enrichment_id_in_aristote)
        print("latest_version: ", latest_version)
        if latest_version.get("status") != "KO":
            return HttpResponse(json.dumps(latest_version), content_type="application/json")
        else:
            return HttpResponse("Enrichment already asked. Wait please.", status=200)   # TODO: change this line
    else:
        return send_enrichment_creation_request(request, aristote, video)
