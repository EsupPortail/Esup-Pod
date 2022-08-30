# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _
from pod.bbb.models import BBB_Meeting as Meeting
from .models import Livestream
from .forms import MeetingForm, LivestreamForm
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
import redis

USE_BBB = getattr(settings, "USE_BBB", False)
USE_BBB_LIVE = getattr(settings, "USE_BBB_LIVE", False)
BBB_NUMBER_MAX_LIVES = getattr(settings, "BBB_NUMBER_MAX_LIVES", 1)


@csrf_protect
@login_required(redirect_field_name="referrer")
@staff_member_required(redirect_field_name="referrer")
def list_meeting(request):
    # Get meetings list, which recordings are available, ordered by date
    meetings_list = Meeting.objects.filter(
        attendee__user_id=request.user.id, recording_available=True
    )
    meetings_list = meetings_list.order_by("-session_date")
    # print(str(meetings_list.query))

    page = request.GET.get("page", 1)

    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(meetings_list, 12)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request,
            "bbb/record_list.html",
            {"records": records, "full_path": full_path},
        )

    return render(
        request,
        "bbb/list_meeting.html",
        {"records": records, "full_path": full_path},
    )


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def publish_meeting(request, id=None):
    # Allows you to create a video from a BigBlueButton presentation

    record = get_object_or_404(Meeting, id=id)

    initial = {
        "id": record.id,
        "meeting_id": record.meeting_id,
        "internal_meeting_id": record.internal_meeting_id,
        "meeting_name": record.meeting_name,
        "recorded": record.recorded,
        "recording_available": record.recording_available,
        "recording_url": record.recording_url,
        "thumbnail_url": record.thumbnail_url,
        "session_date": record.session_date,
    }

    form = MeetingForm(request, initial=initial)

    # Check security : a normal user can publish only a meeting
    # where he was moderator
    meetings_list = Meeting.objects.filter(attendee__user_id=request.user.id, id=id)
    if not meetings_list and not request.user.is_superuser:
        messages.add_message(
            request,
            messages.ERROR,
            _("You aren't the moderator of this BigBlueButton session."),
        )
        raise PermissionDenied

    if request.method == "POST":
        form = MeetingForm(request, request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.id = record.id
            # The 2 parameters are very important in the publish process :
            # At this stage, we put encoding_step=1 (waiting for encoding)
            # and the encoded_by = user that convert this presentation.
            # See the impacts in the models.py, process_recording function.
            # Waiting for encoding
            meeting.encoding_step = 1
            # Save the user that convert this presentation
            meeting.encoded_by = request.user
            meeting.save()
            messages.add_message(
                request,
                messages.INFO,
                _("The BigBlueButton session has been published."),
            )
            return redirect(reverse("bbb:list_meeting"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(request, "bbb/publish_meeting.html", {"record": record, "form": form})


@csrf_protect
@login_required(redirect_field_name="referrer")
@staff_member_required(redirect_field_name="referrer")
def live_list_meeting(request):
    # Get meetings list in progress
    dateSince10Min = timezone.now() - timezone.timedelta(minutes=10)
    meetings_list = Meeting.objects.filter(
        attendee__user_id=request.user.id,
        last_date_in_progress__gte=dateSince10Min,
    )
    meetings_list = meetings_list.order_by("-session_date")
    # print(str(meetings_list.query))

    meetings_list = check_meetings_have_live_in_progress(meetings_list, request)

    # Get number of lives in progress
    lives_in_progress = Livestream.objects.filter(status=1)
    if len(lives_in_progress) >= BBB_NUMBER_MAX_LIVES:
        max_limit_reached = True
    else:
        max_limit_reached = False

    page = request.GET.get("page", 1)

    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(meetings_list, 12)
    try:
        records = paginator.page(page)
    except PageNotAnInteger:
        records = paginator.page(1)
    except EmptyPage:
        records = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request,
            "bbb/live_record_list.html",
            {
                "records": records,
                "full_path": full_path,
                "max_limit_reached": max_limit_reached,
            },
        )

    return render(
        request,
        "bbb/live_list_meeting.html",
        {
            "records": records,
            "full_path": full_path,
            "max_limit_reached": max_limit_reached,
        },
    )


def check_meetings_have_live_in_progress(meetings_list, request):
    # Check if these meetings have a live in progress
    dateToday = timezone.now() - timezone.timedelta(days=1)
    if len(meetings_list) > 0:
        for meeting in meetings_list:
            # Get the live object that corresponds to this meeting in progress
            lives_list = Livestream.objects.filter(
                user_id=request.user.id,
                start_date__gte=dateToday,
                meeting_id=meeting.id,
            )
            if len(lives_list) > 0:
                # Use case : only 1 live for a meeting
                for live in lives_list:
                    # Add the information directly on the meeting
                    # on a specific property live
                    meeting.live = live
    return meetings_list


@csrf_protect
@staff_member_required(redirect_field_name="referrer")
def live_publish_meeting(request, id=None):
    # Allows you to create a live streaming from a BigBlueButton presentation

    record = get_object_or_404(Meeting, id=id)

    initial = {"meeting": record, "status": 0, "end_date": None, "server": None}

    form = LivestreamForm(request, initial=initial)

    # Check security : a normal user can publish only a meeting
    # where he was moderator
    meetings_list = Meeting.objects.filter(attendee__user_id=request.user.id, id=id)
    if not meetings_list and not request.user.is_superuser:
        messages.add_message(
            request,
            messages.ERROR,
            _("You aren't the moderator of this BigBlueButton session."),
        )
        raise PermissionDenied

    if request.method == "POST":
        form = LivestreamForm(request, request.POST)
        if form.is_valid():
            live = form.save(commit=False)
            live.meeting = record
            live.user = request.user
            live.save()
            messages.add_message(
                request,
                messages.INFO,
                _("The BigBlueButton live has been performed."),
            )
            return redirect(reverse("bbb:live_list_meeting"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "bbb/live_publish_meeting.html",
        {"record": record, "form": form},
    )


def live_publish_chat_if_authenticated(user):
    if user.__str__() == "AnonymousUser":
        return False
    return True


@csrf_protect
@user_passes_test(live_publish_chat_if_authenticated, redirect_field_name="referrer")
def live_publish_chat(request, id=None):
    # Allows an authenticated user to send chat question to BBB
    who_sent = "(%s %s) " % (request.user.first_name, request.user.last_name)
    message = request.GET.get("message", None)

    livestreams_list = Livestream.objects.filter(broadcaster_id=id)

    data = {"message_return": "error_no_broadcaster_found", "is_sent": False}
    if len(livestreams_list) > 0:
        for livestream in livestreams_list:
            try:
                # Publish on Redis
                r = redis.Redis(
                    host=livestream.redis_hostname,
                    port=str(livestream.redis_port),
                    db=0,
                )
                r.publish(livestream.redis_channel, who_sent + message)

                data = {"message_return": "message_sent", "is_sent": True}
            except Exception:
                data = {
                    "message_return": "error_no_connection",
                    "is_sent": False,
                }

    return JsonResponse(data)
