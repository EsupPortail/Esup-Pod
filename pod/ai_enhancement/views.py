import json

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from pod.ai_enhancement.forms import AIEnrichmentChoice
from pod.ai_enhancement.models import AIEnrichment
from pod.ai_enhancement.utils import AristoteAI, enrichment_is_already_asked
from pod.main.views import in_maintenance
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


@csrf_protect
def send_enrichment_creation_request(request: WSGIRequest, aristote: AristoteAI, video: Video) -> HttpResponse:
    """Send a request to create an enrichment."""
    creation_response = aristote.create_enrichment_from_url(
        "https://pod.univ-lille.fr/media/videos/585da9d28e5b53c539a1da3ad0d3a3c294a85b5941e9ce46a40b2e006fa69189/35596/360p.mp4",
        # TODO change this
        ["video/mp4"],
        request.user.username,
        "https://webhook.site/da793ba0-5b38-4f80-a1d6-6f472c504f47",  # TODO change this
    )
    if creation_response:
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
            return HttpResponse(
                "Error: ", creation_response["status"],
                status=500,
            )  # TODO create a real error
    return HttpResponse(
        "An error occurred when creating the enrichment.",
        status=500,
    )  # TODO create a real error


@csrf_protect
def enrich_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
    if enrichment_is_already_asked(video):
        enrichment = AIEnrichment.objects.filter(video=video).first()
        latest_version = aristote.get_latest_enrichment_version(enrichment.ai_enrichment_id_in_aristote)
        if enrichment.is_ready:
            return enrich_form(request, video)
        else:
            return HttpResponse("Enrichment already asked. Wait please.", status=200)   # TODO: change this line
    else:
        return send_enrichment_creation_request(request, aristote, video)


def enrich_video_json(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to get the JSON of Aristote version."""
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
    enrichment = AIEnrichment.objects.filter(video=video).first()
    latest_version = aristote.get_latest_enrichment_version(enrichment.ai_enrichment_id_in_aristote)
    return JsonResponse(latest_version)


@csrf_protect
def enrich_form(request: WSGIRequest, video: Video) -> HttpResponse:
    """The view to choose the title of a video with the AI enrichment."""
    form = AIEnrichmentChoice(
        instance=video,
    )
    return render(
        request,
        "choose_video_element/choose_video_title.html",
        {"video": video, "form": form, "page_title": "Enrich with Aristote AI"},
    )
