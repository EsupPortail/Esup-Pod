"""Esup-Pod speaker views."""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from pod.main.views import in_maintenance
from .models import Speaker, Job
from pod.speaker.forms import SpeakerForm, JobForm

from pod.speaker.utils import get_all_speakers
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest


@csrf_protect
@login_required(redirect_field_name="referrer")
def speaker_management(request: WSGIRequest) -> HttpResponse:
    """
    View function for rendering a quiz associated with a video.

    Args:
        request (WSGIRequest): The HTTP request.

    Returns:
        HttpResponse: The HTTP response.
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    speakers = get_all_speakers
    speaker_form = SpeakerForm()
    job_form = JobForm()

    if not (
        request.user.is_superuser or request.user.is_staff
    ):
        messages.add_message(request, messages.ERROR, _("You cannot list speakers."))
        raise PermissionDenied
    
    if (
        not (request.user.is_superuser)
        ):
        messages.add_message(request, messages.ERROR, _("You cannot acces to speaker management."))
        raise PermissionDenied
    if request.method == "POST":
        if request.POST.get("action") and request.POST.get("action") in {
            "add",
            "delete",
            "update",
        }:
            if request.POST["action"] == "add":
                add_speaker(request)
        else:
            messages.add_message(
                request, messages.ERROR, _("An action must be specified.")
            )
        # redirect to remove post data
        return redirect(reverse("speaker:speaker_management"))

    return render(
        request,
        "speakers_management.html",
        {
            "page_title": _("Speakers management"),
            "speakers": speakers,
            "speaker_form": speaker_form,
            "job_form": job_form,
        },
    )


def add_speaker(request):
    """add speaker."""
    try:
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        jobs = request.POST.getlist('jobs[]')
        speaker = Speaker.objects.create(firstname=firstname, lastname=lastname)
        for job_title in jobs:
            if job_title.strip():
                Job.objects.create(title=job_title, speaker=speaker)
        messages.add_message(request, messages.SUCCESS, _("The speaker has been added."))
    except (ValueError, ObjectDoesNotExist):
        messages.add_message(request, messages.ERROR, _("Speaker not found."))

