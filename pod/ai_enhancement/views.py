"""Views for Esup-Pod ai_enhancement module."""

import json
import hashlib
from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from pod.ai_enhancement.forms import (
    AIEnhancementChoice,
    NotifyUserThirdPartyServicesForm,
    NotifyUserDeleteEnhancementForm,
)
from pod.ai_enhancement.models import AIEnhancement
from pod.ai_enhancement.utils import AristoteAI, enhancement_is_already_asked, notify_user
from pod.completion.models import Track
from pod.main.lang_settings import ALL_LANG_CHOICES, PREF_LANG_CHOICES
from pod.main.utils import json_to_web_vtt
from pod.main.views import in_maintenance
from pod.quiz.utils import import_quiz
from pod.video.models import Video, Discipline
from pod.video_encode_transcript.transcript import save_vtt

AI_ENHANCEMENT_CLIENT_ID = getattr(settings, "AI_ENHANCEMENT_CLIENT_ID", "mocked_id")
AI_ENHANCEMENT_CLIENT_SECRET = getattr(
    settings, "AI_ENHANCEMENT_CLIENT_SECRET", "mocked_secret"
)
AI_ENHANCEMENT_TO_STAFF_ONLY = getattr(settings, "AI_ENHANCEMENT_TO_STAFF_ONLY", True)
AI_ENHANCEMENT_PROXY_URL = getattr(settings, "AI_ENHANCEMENT_PROXY_URL", "")
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
        return JsonResponse(
            {"error": "Only application/json content type is allowed."}, status=415
        )
    if "application/json" in request.headers.get("Content-Type"):
        data = json.loads(request.body)
        if "id" in data:
            enhancement = AIEnhancement.objects.filter(
                ai_enhancement_id_in_aristote=data["id"]
            ).first()
            if enhancement:
                if "status" in data and data["status"] == "SUCCESS":
                    enhancement.is_ready = True
                    enhancement.save()
                    notify_user(enhancement.video)
                    return JsonResponse({"status": "OK"}, status=200)
                else:
                    return JsonResponse(
                        {"status": "Enhancement has not yet been successfully achieved."},
                        status=500,
                    )
            else:
                return JsonResponse({"error": "Enhancement not found."}, status=404)
        else:
            return JsonResponse({"error": "No id in the request."}, status=400)


def send_enhancement_creation_request(
    request: WSGIRequest, aristote: AristoteAI, video: Video
) -> HttpResponse:
    """Send a request to create an enhancement."""
    if request.method == "POST":
        form = NotifyUserThirdPartyServicesForm(request.POST)
        if form.is_valid():
            url_scheme = "https" if request.is_secure() else "http"
            mp3_url = video.get_video_mp3().source_file.url
            end_user_identifier = hashlib.sha256(
                (
                    AI_ENHANCEMENT_CLIENT_ID
                    + AI_ENHANCEMENT_CLIENT_SECRET
                    + request.user.username
                ).encode("utf-8")
            ).hexdigest()
            if AI_ENHANCEMENT_PROXY_URL:
                base_url = AI_ENHANCEMENT_PROXY_URL
            else:
                base_url = url_scheme + "://" + get_current_site(request).domain

            creation_response = aristote.create_enhancement_from_url(
                base_url + mp3_url,
                ["video/mp3"],
                end_user_identifier + "@%s" % get_current_site(request).domain,
                base_url + reverse("ai_enhancement:webhook"),
            )
            if creation_response:
                if creation_response["status"] == "OK":
                    AIEnhancement.objects.update_or_create(
                        video=video,
                        ai_enhancement_id_in_aristote=creation_response["id"],
                    )
                    return redirect(reverse("video:video", args=[video.slug]))
                else:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        _("Something wrong… Status error: ")
                        + creation_response["status"],
                    )
            else:
                messages.add_message(
                    request, messages.ERROR, _("Error: no response from Aristote AI.")
                )
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    else:
        form = NotifyUserThirdPartyServicesForm()
    return render(
        request,
        "create_enhancement.html",
        {
            "form": form,
            "video": video,
            "page_title": _("Enhance the video with Aristote AI"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def delete_enhance_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to delete an enhancement."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=video_slug)
    if AI_ENHANCEMENT_TO_STAFF_ONLY and request.user.is_staff is False:
        messages.add_message(
            request, messages.ERROR, _("You cannot delete the video improvement.")
        )
        raise PermissionDenied
    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot delete the video improvement.")
        )
        raise PermissionDenied
    if enhancement_is_already_asked(video):
        #  AIEnhancement.objects.filter(video=video).first().delete()
        enhancement = AIEnhancement.objects.filter(video=video).first()
        if enhancement.is_ready:
            aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
            return delete_enhancement_request(request, aristote, video)
    messages.add_message(request, messages.ERROR, _("The video has not been improved."))
    return redirect(reverse("video:video", args=[video.slug]))


def delete_enhancement_request(
    request: WSGIRequest, aristote: AristoteAI, video: Video
) -> HttpResponse:
    """Send a request to delete an enhancement."""
    if request.method == "POST":
        form = NotifyUserDeleteEnhancementForm(request.POST)
        if form.is_valid():
            enhancement = AIEnhancement.objects.filter(video=video).first()
            if enhancement:
                deletion_response = aristote.delete_enhancement(
                    enhancement.ai_enhancement_id_in_aristote
                )
                if deletion_response:
                    if deletion_response["status"] == "OK":
                        enhancement.delete()
                        messages.add_message(
                            request,
                            messages.SUCCESS,
                            _("Enhancement successfully deleted."),
                        )
                        return redirect(reverse("video:video", args=[video.slug]))
                    else:
                        messages.add_message(
                            request,
                            messages.ERROR,
                            _("Something wrong… Status error: ")
                            + deletion_response["status"],
                        )
                else:
                    messages.add_message(
                        request, messages.ERROR, _("Error: no response from Aristote AI.")
                    )
            else:
                messages.add_message(request, messages.ERROR, _("No enhancement found."))
            return redirect(reverse("video:video", args=[video.slug]))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    else:
        form = NotifyUserDeleteEnhancementForm()
    return render(
        request,
        "delete_enhancement.html",
        {
            "form": form,
            "video": video,
            "page_title": _("Delete the video enhancement"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def enhance_video(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich a video."""
    if in_maintenance():
        return redirect(reverse("maintenance"))
    video = get_object_or_404(Video, slug=video_slug)

    if AI_ENHANCEMENT_TO_STAFF_ONLY and request.user.is_staff is False:
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    if enhancement_is_already_asked(video):
        enhancement = AIEnhancement.objects.filter(video=video).first()
        if enhancement.is_ready:
            return enhance_form(request, video)
    else:
        aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
        return send_enhancement_creation_request(request, aristote, video)


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def enhance_video_json(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to get the JSON of Aristote version."""
    video = get_object_or_404(Video, slug=video_slug)
    if AI_ENHANCEMENT_TO_STAFF_ONLY and request.user.is_staff is False:
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied
    aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
    enhancement = AIEnhancement.objects.filter(video=video).first()
    latest_version = aristote.get_latest_enhancement_version(
        enhancement.ai_enhancement_id_in_aristote
    )
    return JsonResponse(latest_version)


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def enhance_subtitles(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich the subtitles of a video."""
    video = get_object_or_404(Video, slug=video_slug, sites=get_current_site(request))
    if AI_ENHANCEMENT_TO_STAFF_ONLY and request.user.is_staff is False:
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied
    if request.GET.get("src", None) is None:
        aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
        enhancement = AIEnhancement.objects.filter(video=video).first()
        latest_version = aristote.get_latest_enhancement_version(
            enhancement.ai_enhancement_id_in_aristote
        )
        web_vtt = json_to_web_vtt(
            latest_version["transcript"]["sentences"], video.duration
        )
        save_vtt(video, web_vtt, latest_version["transcript"]["language"])
        latest_track = (
            Track.objects.filter(
                video=video,
            )
            .order_by("id")
            .first()
        )
        return redirect(
            reverse("ai_enhancement:enhance_subtitles", args=[video.slug])
            + "?src="
            + str(latest_track.src_id)
            + "&generated="
            + str(True)
        )

    video_folder = video.get_or_create_video_folder()
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
    # AIEnhancement.objects.filter(video=video).delete()
    return redirect(reverse("video:video", args=[video.slug]))


@csrf_protect
@login_required(redirect_field_name="referrer")
def enhance_quiz(request: WSGIRequest, video_slug: str) -> HttpResponse:
    """The view to enrich quiz of a video."""
    video = get_object_or_404(Video, slug=video_slug, sites=get_current_site(request))
    if AI_ENHANCEMENT_TO_STAFF_ONLY and request.user.is_staff is False:
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    if (
        video
        and request.user != video.owner
        and (
            not (request.user.is_superuser or request.user.has_perm("video.change_video"))
        )
        and (request.user not in video.additional_owners.all())
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot use AI to improve this video.")
        )
        raise PermissionDenied

    aristote = AristoteAI(AI_ENHANCEMENT_CLIENT_ID, AI_ENHANCEMENT_CLIENT_SECRET)
    enhancement = AIEnhancement.objects.filter(video=video).first()
    if enhancement:
        latest_version = aristote.get_latest_enhancement_version(
            enhancement.ai_enhancement_id_in_aristote
        )
        multiple_choice_questions_json = latest_version["multipleChoiceQuestions"]

    if enhancement_is_already_asked(video):
        enhancement = AIEnhancement.objects.filter(video=video).first()
        if enhancement.is_ready:
            multiple_choice_questions_json = latest_version["multipleChoiceQuestions"]

            questions_dict = {"multiple_choice": multiple_choice_questions_json}

            import_quiz(video, json.dumps(questions_dict))

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Quiz successfully imported."),
            )
            return redirect(reverse("quiz:edit_quiz", args=[video.slug]))

    return redirect(reverse("video:video", args=[video.slug]))


def enhance_form(request: WSGIRequest, video: Video) -> HttpResponse:
    """The view to choose the title of a video with the AI enhancement."""
    if request.method == "POST":
        form = AIEnhancementChoice(request.POST, instance=video)
        if form.is_valid():
            disciplines = video.discipline.all()
            form.save()
            discipline = Discipline.objects.filter(
                title=form.cleaned_data["disciplines"]
            ).first()
            for dis in disciplines:
                video.discipline.add(dis)
            if discipline in Discipline.objects.all():
                video.discipline.add(discipline)
            video.save()
            if request.POST.get("_saveandback", None) is not None:
                return redirect(reverse("video:video", args=[video.slug]))
            return redirect(
                reverse("ai_enhancement:enhance_subtitles", args=[video.slug])
            )
        else:
            return render(
                request,
                "choose_video_element.html",
                {
                    "video": video,
                    "form": form,
                    "page_title": _("Enhance the video with Aristote AI"),
                },
            )
    else:
        form = AIEnhancementChoice(
            instance=video,
        )
        return render(
            request,
            "choose_video_element.html",
            {
                "video": video,
                "form": form,
                "page_title": _("Enhance the video with Aristote AI"),
            },
        )


'''
def check_video_generated(request: WSGIRequest, video: Video) -> None:
    """Check if the video is generated and delete the enhancement if it is."""
    if enhancement_is_already_asked(video) and request.GET.get("generated") == "True":
        AIEnhancement.objects.filter(video=video).first().delete()
'''
