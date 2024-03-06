import json

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from pod.ai_enhancement.forms import AIEnrichmentChoice
from pod.ai_enhancement.models import AIEnrichment
from pod.ai_enhancement.utils import AristoteAI, enrichment_is_already_asked, json_to_web_vtt
from pod.completion.models import Track
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES
from pod.main.views import in_maintenance
from pod.podfile.models import UserFolder
from pod.video.models import Video, Discipline
from pod.video_encode_transcript.transcript import saveVTT

AI_ENRICHMENT_CLIENT_ID = getattr(settings, "AI_ENRICHMENT_CLIENT_ID", "mocked_id")
AI_ENRICHMENT_CLIENT_SECRET = getattr(settings, "AI_ENRICHMENT_CLIENT_SECRET", "mocked_secret")
LANG_CHOICES = getattr(
    settings,
    "LANG_CHOICES",
    (
        (_("-- Frequently used languages --"), PREF_LANG_CHOICES),
        (_("-- All languages --"), ALL_LANG_CHOICES),
    ),
)
__LANG_CHOICES_DICT__ = {
    key: value for key, value in LANG_CHOICES[0][1] + LANG_CHOICES[1][1]
}


@csrf_exempt
def toggle_webhook(request: WSGIRequest):
    """Receive webhook from the AI Enhancement service."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)
    if "application/json" not in request.headers.get("Content-Type"):
        return JsonResponse({"error": "Only application/json content type is allowed."}, status=415)
    if "application/json" in request.headers.get("Content-Type"):
        data = json.loads(request.body)
        if "id" in data:
            enrichment = AIEnrichment.objects.filter(ai_enrichment_id_in_aristote=data["id"]).first()
            if enrichment:
                if "status" in data and data["status"] == "SUCCESS":
                    enrichment.is_ready = True
                    enrichment.save()
                    return JsonResponse({"status": "OK"}, status=200)
                else:
                    return JsonResponse({"status": "Enrichment has not yet been successfully achieved."}, status=500)
            else:
                return JsonResponse({"error": "Enrichment not found."}, status=404)
        else:
            return JsonResponse({"error": "No id in the request."}, status=400)


@csrf_protect
def send_enrichment_creation_request(request: WSGIRequest, aristote: AristoteAI, video: Video) -> HttpResponse:
    """Send a request to create an enrichment."""
    creation_response = aristote.create_enrichment_from_url(
        "https://pod.univ-lille.fr/media/videos/585da9d28e5b53c539a1da3ad0d3a3c294a85b5941e9ce46a40b2e006fa69189/35596/360p.mp4",
        # TODO change this
        ["video/mp4"],
        request.user.username,
        "https://webhook.site/02dce66d-1bb1-42dd-b204-39fb4df27b94",  # TODO change this
    )
    if creation_response:
        if creation_response["status"] == "OK":
            AIEnrichment.objects.create(
                video=video,
                ai_enrichment_id_in_aristote=creation_response["id"],
            )
            return redirect(reverse("video:video", args=[video.slug]))
        else:
            raise Exception("Error: ", creation_response["status"])
    else:
        raise Exception("Error: no response from Aristote AI.")


@csrf_protect
def enrich_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
    if enrichment_is_already_asked(video):
        enrichment = AIEnrichment.objects.filter(video=video).first()
        if enrichment.is_ready:
            return enrich_form(request, video)
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
def enrich_subtitles(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich the subtitles of a video."""
    # AIEnrichment.objects.filter(video=video).delete()
    video = get_object_or_404(Video, slug=video_slug, sites=get_current_site(request))
    video_folder, created = UserFolder.objects.get_or_create(
        name=video.slug,
        owner=request.user,
    )
    if enrichment_is_already_asked(video):
        enrichment = AIEnrichment.objects.filter(video=video).first()
        if enrichment.is_ready:
            return render(
                request,
                "video_caption_maker.html",
                {
                    "current_folder": video_folder,
                    "video": video,
                    "languages": LANG_CHOICES,
                    "page_title": _("Video Caption Maker - Aristote AI Version"),
                    # "ai_enrichment": enrichment,
                },
            )
        return redirect(reverse("video:video", args=[video.slug]))
    return redirect(reverse("video:video", args=[video.slug]))


@csrf_protect
def enrich_form(request: WSGIRequest, video: Video) -> HttpResponse:
    """The view to choose the title of a video with the AI enrichment."""
    if request.method == "POST":
        form = AIEnrichmentChoice(request.POST, instance=video)
        if form.is_valid():
            disciplines = video.discipline.all()
            form.save()
            discipline = Discipline.objects.filter(title=form.cleaned_data["disciplines"]).first()
            for dis in disciplines:
                video.discipline.add(dis)
            if discipline in Discipline.objects.all():
                video.discipline.add(discipline)
            video.save()
            video = form.instance
            aristote = AristoteAI(AI_ENRICHMENT_CLIENT_ID, AI_ENRICHMENT_CLIENT_SECRET)
            enrichment = AIEnrichment.objects.filter(video=video).first()
            latest_version = aristote.get_latest_enrichment_version(enrichment.ai_enrichment_id_in_aristote)
            web_vtt = json_to_web_vtt(latest_version["transcript"]["sentences"], video.duration)
            saveVTT(video, web_vtt, latest_version["transcript"]["language"])
            latest_track = Track.objects.filter(video=video,).order_by("id").first()
            return redirect(reverse("ai_enhancement:enrich_subtitles", args=[video.slug]) + '?src=' + str(latest_track.src_id))
        else:
            return render(
                request,
                "choose_video_element.html",
                {"video": video, "form": form, "page_title": "Enrich with Aristote AI"},
            )
    else:
        form = AIEnrichmentChoice(
            instance=video,
        )
        return render(
            request,
            "choose_video_element.html",
            {"video": video, "form": form, "page_title": "Enrich with Aristote AI"},
        )
