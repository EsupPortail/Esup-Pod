"""Esup-Pod speaker views."""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
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
from django.db import transaction


@csrf_protect
@login_required(redirect_field_name="referrer")
def speaker_management(request: WSGIRequest) -> HttpResponse:
    if in_maintenance():
        return redirect(reverse("maintenance"))

    if not request.user.is_superuser:
        messages.add_message(request, messages.ERROR, _("You cannot access speaker management."))
        raise PermissionDenied

    if request.method == "POST":
        if handle_speaker_action(request):
            return redirect(reverse("speaker:speaker_management"))

    speakers = get_all_speakers
    speaker_form = SpeakerForm()
    job_form = JobForm()

    return render(
        request,
        "speaker/speakers_management.html",
        {
            "page_title": _("Speakers management"),
            "speakers": speakers,
            "speaker_form": speaker_form,
            "job_form": job_form,
        },
    )


def handle_speaker_action(request):
    action = request.POST.get("action")
    if action == "add":
        return add_speaker(request)
    elif action == "delete":
        return delete_speaker(request)
    elif action == "edit":
        return edit_speaker(request)
    else:
        messages.add_message(request, messages.ERROR, _("An action must be specified."))
        return False


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
        return True
    except (ValueError, ObjectDoesNotExist):
        messages.add_message(request, messages.ERROR, _("Speaker not found."))
        return False


def delete_speaker(request):
    """Remove speaker and jobs."""
    try:
        speakerid = request.POST.get('speakerid')
        Speaker.objects.get(id=speakerid).delete()
        messages.add_message(request, messages.SUCCESS, _("The speaker has been deleted."))
        return True
    except (ValueError, ObjectDoesNotExist):
        messages.add_message(request, messages.ERROR, _("Speaker not found."))
        return False


@login_required
def edit_speaker(request):
    try:
        job_ids = request.POST.getlist('jobIds[]')
        job_titles = request.POST.getlist('jobs[]')

        with transaction.atomic():
            speaker = edit_speaker_details(request)
            update_existing_jobs(speaker, job_ids, job_titles)

        messages.add_message(request, messages.SUCCESS, _("The speaker has been updated."))
        return True
    except (ValueError, ObjectDoesNotExist) as e:
        messages.add_message(request, messages.ERROR, _("Speaker not found or invalid input."))
        print(e)
        return False


def edit_speaker_details(request):
    speakerid = request.POST.get('speakerid')
    firstname = request.POST.get('firstname')
    lastname = request.POST.get('lastname')

    if not speakerid or not firstname or not lastname:
        raise ValueError("Missing speaker information")

    speaker = Speaker.objects.get(id=speakerid)
    speaker.firstname = firstname
    speaker.lastname = lastname
    speaker.save()

    return speaker


def update_existing_jobs(speaker, job_ids, job_titles):
    existing_jobs = {job.id: job for job in speaker.job_set.all()}
    updated_job_ids = {int(job_id) for job_id in job_ids if job_id}

    # Remove jobs that are not in the updated list
    jobs_to_remove = set(existing_jobs.keys()) - updated_job_ids
    for job_id in jobs_to_remove:
        job = existing_jobs[job_id]
        job.delete()

    # Add or update jobs
    for job_id, job_title in zip(job_ids, job_titles):
        job_title = job_title.strip()
        if job_id:
            job_id = int(job_id)
            if job_id in existing_jobs:
                job = existing_jobs[job_id]
                job.title = job_title
                job.save()
        else:
            if job_title:
                Job.objects.create(title=job_title, speaker=speaker)


@login_required
def get_speaker(request, speaker_id):
    """Get details of a specific speaker including jobs."""
    speaker = get_object_or_404(Speaker, id=speaker_id)
    jobs = speaker.job_set.all().values('id', 'title')
    speaker_data = {
        'id': speaker.id,
        'firstname': speaker.firstname,
        'lastname': speaker.lastname,
        'jobs': list(jobs)
    }
    return JsonResponse({'speaker': speaker_data})


@login_required
def get_jobs(request, speaker_id):
    speaker = get_object_or_404(Speaker, id=speaker_id)
    jobs = speaker.job_set.all().values('id', 'title')
    jobs_list = list(jobs)
    return JsonResponse({'jobs': jobs_list})
