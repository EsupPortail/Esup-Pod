import json

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt

from pod.ai_enhancement.forms import AIEnhancementChoice, NotifyUserThirdPartyServicesForm
from pod.ai_enhancement.models import AIEnhancement
from pod.ai_enhancement.utils import AristoteAI, enhancement_is_already_asked
from pod.completion.models import Track
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES
from pod.main.utils import json_to_web_vtt
from pod.main.views import in_maintenance
from pod.podfile.models import UserFolder
from pod.video.models import Video, Discipline
from pod.video_encode_transcript.transcript import saveVTT

AI_ENHANCEMENT_CLIENT_ID = getattr(settings, "AI_ENHANCEMENT_CLIENT_ID", "mocked_id")
AI_ENHANCEMENT_CLIENT_SECRET = getattr(settings, "AI_ENHANCEMENT_CLIENT_SECRET", "mocked_secret")
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
            enhancement = AIEnhancement.objects.filter(ai_enhancement_id_in_aristote=data["id"]).first()
            if enhancement:
                if "status" in data and data["status"] == "SUCCESS":
                    enhancement.is_ready = True
                    enhancement.save()
                    return JsonResponse({"status": "OK"}, status=200)
                else:
                    return JsonResponse({"status": "Enrichment has not yet been successfully achieved."}, status=500)
            else:
                return JsonResponse({"error": "Enrichment not found."}, status=404)
        else:
            return JsonResponse({"error": "No id in the request."}, status=400)


@csrf_protect
def send_enhancement_creation_request(request: WSGIRequest, aristote: AristoteAI, video: Video) -> HttpResponse:
    """Send a request to create an enhancement."""
    if request.method == "POST":
        form = NotifyUserThirdPartyServicesForm(request.POST)
        if form.is_valid():
            creation_response = aristote.create_enhancement_from_url(
                get_current_site(request).domain + video.video.url,
                ["video/mp4"],
                request.user.username,
                reverse("ai_enhancement:webhook"),
            )
            if creation_response:
                if creation_response["status"] == "OK":
                    AIEnhancement.objects.create(
                        video=video,
                        ai_enhancement_id_in_aristote=creation_response["id"],
                    )
                    return redirect(reverse("video:video", args=[video.slug]))
                else:
                    raise Exception("Error: ", creation_response["status"])
            else:
                raise Exception("Error: no response from Aristote AI.")
        else:
            messages.add_message(request, messages.ERROR, _("One or more errors have been found in the form."))
    else:
        form = NotifyUserThirdPartyServicesForm()
    return render(
        request,
        "create_enhancement.html",
        {
            "form": form,
            "video": video,
            "page_title": _("Enhance the video with Aristote AI"),
        }
    )


@csrf_protect
def enhance_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
    if enhancement_is_already_asked(video):
        enhancement = AIEnhancement.objects.filter(video=video).first()
        if enhancement.is_ready:
            return enhance_form(request, video)
    else:
        return send_enhancement_creation_request(request, aristote, video)


def enhance_video_json(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to get the JSON of Aristote version."""
    video = get_object_or_404(Video, slug=video_slug)
    aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
    enhancement = AIEnhancement.objects.filter(video=video).first()
    latest_version = aristote.get_latest_enhancement_version(enhancement.ai_enhancement_id_in_aristote)
    return JsonResponse(latest_version)


@csrf_protect
def enhance_subtitles(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich the subtitles of a video."""
    video = get_object_or_404(Video, slug=video_slug, sites=get_current_site(request))
    video_folder, created = UserFolder.objects.get_or_create(
        name=video.slug,
        owner=request.user,
    )
    if enhancement_is_already_asked(video):
        enhancement = AIEnhancement.objects.filter(video=video).first()
        if enhancement.is_ready:
            return render(
                request,
                "video_caption_maker.html",
                {
                    "current_folder": video_folder,
                    "video": video,
                    "languages": LANG_CHOICES,
                    "page_title": _("Video Caption Maker - Aristote AI Version"),
                    # "ai_enhancement": enhancement,
                },
            )
    AIEnhancement.objects.filter(video=video).delete()
    return redirect(reverse("video:video", args=[video.slug]))


@csrf_protect
def enhance_form(request: WSGIRequest, video: Video) -> HttpResponse:
    """The view to choose the title of a video with the AI enhancement."""
    if request.method == "POST":
        form = AIEnhancementChoice(request.POST, instance=video)
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
            aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
            enhancement = AIEnhancement.objects.filter(video=video).first()
            latest_version = aristote.get_latest_enhancement_version(enhancement.ai_enhancement_id_in_aristote)
            web_vtt = json_to_web_vtt(latest_version["transcript"]["sentences"], video.duration)
            saveVTT(video, web_vtt, latest_version["transcript"]["language"])
            latest_track = Track.objects.filter(video=video,).order_by("id").first()
            return redirect(reverse("ai_enhancement:enhance_subtitles", args=[video.slug]) + '?src=' + str(latest_track.src_id))
        else:
            return render(
                request,
                "choose_video_element.html",
                {"video": video, "form": form, "page_title": _("Enrich with Aristote AI")},
            )
    else:
        form = AIEnhancementChoice(
            instance=video,
        )
        return render(
            request,
            "choose_video_element.html",
            {"video": video, "form": form, "page_title": _("Enrich with Aristote AI")},
        )
