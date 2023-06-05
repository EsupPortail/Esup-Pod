"""Views of the Meeting module."""
import os
import bleach
import requests

# from django.utils.dateparse import parse_duration
# from datetime import datetime as dt

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import datetime

from html.parser import HTMLParser
import shutil
from pod.video.models import Video
from pod.video.models import Type

from .models import Meeting, StatelessRecording, Recording
from .utils import get_nth_week_number
from .forms import MeetingForm, MeetingDeleteForm, MeetingPasswordForm
from .forms import MeetingInviteForm, RecordingForm
from pod.main.views import in_maintenance, TEMPLATE_VISIBLE_SETTINGS
from pod.main.utils import display_message_with_icon

# For Youtube download
from pytube import YouTube
from pytube.exceptions import PytubeError, VideoUnavailable

# For PeerTube download
import json

RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY", False
)
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
DEFAULT_MEETING_THUMBNAIL = getattr(
    settings, "DEFAULT_MEETING_THUMBNAIL", "img/default-meeting.svg"
)
BBB_MEETING_INFO = getattr(
    settings,
    "BBB_MEETING_INFO",
    {
        "meetingName": _("Meeting name"),
        "hasUserJoined": _("Has user joined?"),
        "recording": _("Recording"),
        "participantCount": _("Participant count"),
        "listenerCount": _("Listener count"),
        "moderatorCount": _("Moderator count"),
        "attendees": _("Attendees"),
        "attendee": _("Attendee"),
        "fullName": _("Full name"),
        "role": _("Role"),
    },
)
MEETING_DISABLE_RECORD = getattr(settings, "MEETING_DISABLE_RECORD", True)

DEFAULT_TYPE_ID = getattr(settings, "DEFAULT_TYPE_ID", 1)

VIDEO_ALLOWED_EXTENSIONS = getattr(
    settings,
    "VIDEO_ALLOWED_EXTENSIONS",
    (
        "3gp",
        "avi",
        "divx",
        "flv",
        "m2p",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "mts",
        "wmv",
        "mp3",
        "ogg",
        "wav",
        "wma",
        "webm",
        "ts",
    ),
)

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)


@login_required(redirect_field_name="referrer")
def my_meetings(request):
    site = get_current_site(request)
    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "meeting/my_meetings.html", {"access_not_allowed": True})
    if request.GET and request.GET.get("all") == "true":
        meetings = request.user.owner_meeting.all().filter(
            site=site
        ) | request.user.owners_meetings.all().filter(site=site)
        meetings = meetings.distinct()
    else:
        # remove past meeting
        meetings = [
            meeting
            for meeting in (request.user.owner_meeting.all().filter(site=site))
            if meeting.is_active
        ]
    return render(
        request,
        "meeting/my_meetings.html",
        {
            "meetings": meetings,
            "page_title": _("My meetings"),
            "DEFAULT_MEETING_THUMBNAIL": static(DEFAULT_MEETING_THUMBNAIL),
            "meeting_disable_record": MEETING_DISABLE_RECORD,
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def add_or_edit(request, meeting_id=None):
    if in_maintenance():
        return redirect(reverse("maintenance"))
    meeting = (
        get_object_or_404(Meeting, meeting_id=meeting_id, site=get_current_site(request))
        if meeting_id
        else None
    )
    if (
        meeting
        and request.user != meeting.owner
        and (
            not (
                request.user.is_superuser
                or request.user.has_perm("meeting.change_meeting")
            )
        )
        and (request.user not in meeting.additional_owners.all())
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot edit this meeting.")
        )
        raise PermissionDenied

    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "meeting/add_or_edit.html", {"access_not_allowed": True})

    default_owner = meeting.owner.pk if meeting else request.user.pk
    form = MeetingForm(
        instance=meeting,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": default_owner},
    )

    if request.method == "POST":
        form = MeetingForm(
            request.POST,
            instance=meeting,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user,
            current_lang=request.LANGUAGE_CODE,
        )
        if form.is_valid():
            meeting = save_meeting_form(request, form)
            display_message_with_icon(
                request, messages.INFO, _("The changes have been saved.")
            )
            return redirect(reverse("meeting:my_meetings"))
        else:
            display_message_with_icon(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    page_title = (
        "%s <b>%s</b>" % (_("Edit the meeting"), meeting.name)
        if meeting
        else _("Add a new meeting")
    )
    return render(
        request,
        "meeting/add_or_edit.html",
        {"form": form, "page_title": mark_safe(page_title)},
    )


def save_meeting_form(request, form):
    meeting = form.save(commit=False)
    meeting.site = get_current_site(request)
    if (
        (request.user.is_superuser or request.user.has_perm("meeting.add_meeting"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
    ):
        meeting.owner = form.cleaned_data["owner"]

    elif getattr(meeting, "owner", None) is None:
        meeting.owner = request.user
    meeting.save()
    form.save_m2m()
    return meeting


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def delete(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot delete this meeting.")
        )
        raise PermissionDenied

    form = MeetingDeleteForm()

    if request.method == "POST":
        form = MeetingDeleteForm(request.POST)
        if form.is_valid():
            meeting.delete()
            display_message_with_icon(
                request, messages.INFO, _("The meeting has been deleted.")
            )
            return redirect(reverse("meeting:my_meetings"))
        else:
            display_message_with_icon(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(request, "meeting/delete.html", {"meeting": meeting, "form": form})


@csrf_protect
@ensure_csrf_cookie
def join(request, meeting_id, direct_access=None):
    try:
        id = int(meeting_id[: meeting_id.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid meeting id")
    meeting = get_object_or_404(Meeting, id=id, site=get_current_site(request))

    if request.user.is_authenticated and (
        request.user == meeting.owner or request.user in meeting.additional_owners.all()
    ):
        return join_as_moderator(request, meeting)

    if direct_access and direct_access != meeting.get_hashkey():
        raise SuspiciousOperation("Invalid access")

    if meeting.get_is_meeting_running() is not True:
        return render(
            request,
            "meeting/join.html",
            {"meeting": meeting, "form": None},
        )

    show_page = get_meeting_access(request, meeting)

    return render_show_page(request, meeting, show_page, direct_access)


def render_show_page(request, meeting, show_page, direct_access):
    if show_page and direct_access and request.user.is_authenticated:
        # join as attendee
        # get user name and redirect to BBB
        fullname = (
            request.user.get_full_name()
            if (request.user.get_full_name() != "")
            else request.user.get_username()
        )
        join_url = meeting.get_join_url(fullname, "VIEWER", request.user.get_username())
        return redirect(join_url)
    if show_page:
        remove_password_in_form = direct_access is not None
        return check_form(request, meeting, remove_password_in_form)
    else:
        return check_user(request)
    """
    return render(
        request,
        "meeting/join.html",
        {"meeting": meeting, "form": form},
    )
    """


def join_as_moderator(request, meeting):
    try:
        created = meeting.create(request)
        if created:
            # get user name and redirect to BBB with moderator rights
            fullname = (
                request.user.get_full_name()
                if (request.user.get_full_name() != "")
                else request.user.get_username()
            )
            join_url = meeting.get_join_url(
                fullname, "MODERATOR", request.user.get_username()
            )
            return redirect(join_url)
        else:
            msg = "Unable to create meeting ! "
            display_message_with_icon(request, messages.ERROR, msg)
            return render(
                request,
                "meeting/join.html",
                {"meeting": meeting, "form": None},
            )
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        for key in args:
            msg += "<b>%s:</b> %s<br/>" % (key, args[key])
        display_message_with_icon(request, messages.ERROR, mark_safe(msg))
        return render(
            request,
            "meeting/join.html",
            {"meeting": meeting, "form": None},
        )


def check_user(request):
    if request.user.is_authenticated:
        display_message_with_icon(
            request, messages.ERROR, _("You cannot access to this meeting.")
        )
        raise PermissionDenied
    else:
        return redirect("%s?referrer=%s" % (settings.LOGIN_URL, request.get_full_path()))


def check_form(request, meeting, remove_password_in_form):
    current_user = request.user if request.user.is_authenticated else None
    form = MeetingPasswordForm(
        current_user=current_user,
        remove_password=remove_password_in_form,
    )
    if request.method == "POST":
        form = MeetingPasswordForm(
            request.POST,
            current_user=current_user,
            remove_password=remove_password_in_form,
        )
        if form.is_valid():
            access_granted = remove_password_in_form or (
                not remove_password_in_form
                and form.cleaned_data["password"] == meeting.attendee_password
            )
            if access_granted:
                # get user name from form and redirect to BBB
                join_url = ""
                if current_user:
                    fullname = (
                        request.user.get_full_name()
                        if (request.user.get_full_name() != "")
                        else request.user.get_username()
                    )
                    join_url = meeting.get_join_url(
                        fullname, "VIEWER", request.user.get_username()
                    )
                else:
                    fullname = form.cleaned_data["name"]
                    join_url = meeting.get_join_url(fullname, "VIEWER")
                return redirect(join_url)
            else:
                display_message_with_icon(
                    request,
                    messages.ERROR,
                    _("Password given is not correct."),
                )
        else:
            display_message_with_icon(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    return render(
        request,
        "meeting/join.html",
        {"meeting": meeting, "form": form},
    )


def is_in_meeting_groups(user, meeting):
    return user.owner.accessgroup_set.filter(
        code_name__in=[
            name[0] for name in meeting.restrict_access_to_groups.values_list("code_name")
        ]
    ).exists()


def get_meeting_access(request, meeting):
    """Return True if access is granted to current user."""
    is_restricted = meeting.is_restricted
    is_restricted_to_group = meeting.restrict_access_to_groups.all().exists()
    is_access_protected = is_restricted or is_restricted_to_group
    if is_access_protected:
        access_granted_for_restricted = (
            request.user.is_authenticated and not is_restricted_to_group
        )
        access_granted_for_group = request.user.is_authenticated and is_in_meeting_groups(
            request.user, meeting
        )
        return (is_restricted and access_granted_for_restricted) or (
            is_restricted_to_group and access_granted_for_group
        )
    else:
        return True


@csrf_protect
@ensure_csrf_cookie
# @login_required(redirect_field_name="referrer")
def status(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )
    """
    if request.user != meeting.owner and not (
        request.user.is_superuser
        or request.user.has_perm("meeting.delete_meeting")
    ):
        messages.add_message(
            request, messages.ERROR, _("You cannot delete this meeting.")
        )
        raise PermissionDenied
    """
    return JsonResponse({"status": meeting.get_is_meeting_running()}, safe=False)


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def end(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot delete this meeting.")
        )
        raise PermissionDenied
    msg = ""
    try:
        meeting.end()
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        for key in args:
            msg += "<b>%s:</b> %s<br>" % (key, args[key])
        msg = mark_safe(msg)
    if request.is_ajax():
        return JsonResponse({"end": meeting.end(), "msg": msg}, safe=False)
    else:
        if msg != "":
            display_message_with_icon(request, messages.ERROR, msg)
        return redirect(reverse("meeting:my_meetings"))


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def get_meeting_info(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot delete this meeting.")
        )
        raise PermissionDenied
    msg = ""
    info = {}
    try:
        meeting_info = meeting.get_meeting_info()
        info = get_meeting_info_json(meeting_info)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        for key in args:
            msg += "<b>%s:</b> %s<br>" % (key, args[key])
        msg = mark_safe(msg)
    if request.is_ajax():
        return JsonResponse({"info": info, "msg": msg}, safe=False)
    else:
        if msg != "":
            display_message_with_icon(request, messages.ERROR, msg)
        return JsonResponse({"info": info, "msg": msg}, safe=False)


@login_required(redirect_field_name="referrer")
def internal_recordings(request, meeting_id):
    """List the internal recordings.

    Args:
        request (Request): HTTP request
        meeting_id (String): meeting id (BBB format)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTPResponse: internal recordings list
    """
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    # Secure the list of internal recordings
    secure_internal_recordings(request, meeting)

    # Additional owners can't delete these recordings
    can_delete = get_can_delete_recordings(request, meeting)

    meeting_recordings = meeting.get_recordings()
    recordings = []
    if type(meeting_recordings.get("recordings")) is dict:
        for data in meeting_recordings["recordings"].values():
            # Management of the BBB recording
            bbb_recording = StatelessRecording(
                data["recordID"], data["name"], data["state"]
            )
            # Init rights
            bbb_recording.canUpload = False

            bbb_recording.startTime = data["startTime"]
            bbb_recording.endTime = data["endTime"]
            for playback in data["playback"]:
                if data["playback"][playback]["type"] == "presentation":
                    bbb_recording.presentationUrl = data["playback"][playback]["url"]

                # Uploading to Pod is possible only for video playback
                if data["playback"][playback]["type"] == "video":
                    bbb_recording.canUpload = True
                    bbb_recording.videoUrl = data["playback"][playback]["url"]

            # Only the owner can delete their recordings
            bbb_recording.canDelete = can_delete
            # Search for more informations from database (if already uploaded to Pod)
            recording = Recording.objects.filter(
                recording_id=data["recordID"], is_internal=True
            ).first()
            if recording:
                bbb_recording.uploadedToPodBy = recording.uploaded_to_pod_by
            recordings.append(bbb_recording)

    return render(
        request,
        "meeting/internal_recordings.html",
        {
            "meeting": meeting,
            "recordings": recordings,
            "page_title": _("Meeting recordings"),
        },
    )


def secure_post_request(request):
    """Secure that this request is POST type.

    Args:
        request (Request): HTTP request

    Raises:
        PermissionDenied: if method not POST
    """
    if request.method != "POST":
        display_message_with_icon(
            request, messages.WARNING, _("This view cannot be accessed directly.")
        )
        raise PermissionDenied


def secure_internal_recordings(request, meeting):
    """Secure the internal recordings of a meeting.

    Args:
        request (Request): HTTP request
        meeting (Meeting): Meeting instance

    Raises:
        PermissionDenied: if user not allowed
    """
    if (
        meeting
        and request.user != meeting.owner
        and not (
            request.user.is_superuser or request.user.has_perm("meeting.view_meeting")
        )
        and (request.user not in meeting.additional_owners.all())
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot view the recordings of this meeting.")
        )
        raise PermissionDenied


def secure_external_recording(request, recording):
    """Secure an external recording.

    Args:
        request (Request): HTTP request
        recording (Recording): Recording instance

    Raises:
        PermissionDenied: if user not allowed
    """
    if (
        recording
        and request.user != recording.owner
        and not (
            request.user.is_superuser or request.user.has_perm("meeting.view_recording")
        )
        and (request.user not in recording.additional_owners.all())
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot view this recording.")
        )
        raise PermissionDenied


def secure_request_for_upload(request):
    """Check that the request is correct for uploading a recording.

    Args:
        request (Request): HTTP request

    Raises:
        ValueError: if bad data
    """
    # Source_url and recording_name are necessary
    if request.POST.get("source_url") == "" or request.POST.get("recording_name") == "":
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the video")
        msg["message"] = _("No URL found / No recording name")
        msg["proposition"] = _(
            "Try changing the record type or address for this recording"
        )
        raise ValueError(msg)


def get_can_delete_recordings(request, meeting):
    """Check if user can delete, or not, a recording of this meeting.

    Args:
        request (Request): HTTP request
        meeting (Meeting): Meeting instance

    Returns:
        Boolean: True if current user can delete the recordings of this meeting.
    """
    can_delete = False

    # Additional owners can't delete these recordings
    if (
        request.user == meeting.owner
        or (request.user.is_superuser)
        or (request.user.has_perm("meeting.delete_meeting"))
    ):
        can_delete = True
    return can_delete


def get_can_delete_external_recording(request, owner):
    """Return True if current user can delete this recording."""
    can_delete = False

    # Only owner can delete this external recording
    if (
        request.user == owner
        or (request.user.is_superuser)
        or (request.user.has_perm("meeting.delete_external_recording"))
    ):
        can_delete = True
    return can_delete


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def delete_internal_recording(request, meeting_id, recording_id):
    """Delete an internal recording.

    Args:
        request (Request): HTTP request
        meeting_id (String): meeting id (BBB format)
        recording_id (String): recording id (BBB format)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the recordings list
    """
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    # Secure internal recording
    secure_internal_recordings(request, meeting)

    # Only POST request
    secure_post_request(request)

    msg = ""
    delete = False
    try:
        delete = meeting.delete_recording(recording_id)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        for key in args:
            msg += "<b>%s:</b> %s<br/>" % (key, args[key])
        msg = mark_safe(msg)
    if delete and msg == "":
        display_message_with_icon(
            request, messages.INFO, _("The recording has been deleted.")
        )
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:internal_recordings", args=(meeting.meeting_id,)))


def get_meeting_info_json(info):
    response = {}
    for key in info:
        temp_key = key.split("__")[0] if "__" in key else key
        if BBB_MEETING_INFO.get(temp_key):
            response_key = "%s" % BBB_MEETING_INFO.get(temp_key)
            if temp_key != key:
                response_key = response_key + " %s" % key.split("__")[1]
            if type(info[key]) is str:
                response[response_key] = info[key]
            if type(info[key]) is dict:
                response[response_key] = get_meeting_info_json(info[key])
    return response


def end_callback(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )
    meeting.is_running = False
    meeting.save()
    return HttpResponse()


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def invite(request, meeting_id):
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot invite for this meeting.")
        )
        raise PermissionDenied
    form = MeetingInviteForm()
    if request.method == "POST":
        form = MeetingInviteForm(request.POST)

        if form.is_valid():
            emails = get_dest_emails(meeting, form)
            send_invite(request, meeting, emails)
            display_message_with_icon(
                request, messages.INFO, _("Invitations send to recipients.")
            )
            return redirect(reverse("meeting:my_meetings"))
    return render(
        request,
        "meeting/invite.html",
        {"meeting": meeting, "form": form},
    )


def get_dest_emails(meeting, form):
    emails = form.cleaned_data["emails"]
    if form.cleaned_data["owner_copy"] is True:
        emails.append(meeting.owner.email)
        for add_owner in meeting.additional_owners.all():
            emails.append(add_owner.email)
    return emails


def send_invite(request, meeting, emails):
    subject = _("%(owner)s invites you to the meeting %(meeting_title)s") % {
        "owner": meeting.owner.get_full_name(),
        "meeting_title": meeting.name,
    }
    from_email = meeting.owner.email  # DEFAULT_FROM_EMAIL
    html_content = get_html_content(request, meeting)
    text_content = bleach.clean(html_content, tags=[], strip=True)
    msg = EmailMultiAlternatives(subject, text_content, from_email, emails)
    msg.attach_alternative(html_content, "text/html")
    # ics calendar
    ics_content = create_ics(request, meeting)

    filename_event = "/tmp/invite-%d.ics" % meeting.id
    with open(filename_event, "w") as ics_file:
        ics_file.writelines(ics_content)

    msg.attach_file(filename_event, "text/calendar")
    msg.send()
    os.remove(filename_event)


def get_html_content(request, meeting):
    join_link = request.build_absolute_uri(
        reverse("meeting:join", args=(meeting.meeting_id,))
    )
    meeting_start_datetime = timezone.localtime(meeting.start_at).strftime(
        "%d/%m/%Y %H:%M"
    )
    full_name = (
        meeting.owner.get_full_name()
        if (meeting.owner.get_full_name() != "")
        else meeting.owner.username
    )
    if meeting.recurrence:
        html_content = (
            _(
                """
            <p>Hello,</p>
            <p>%(owner)s invites you to a recurring meeting %(meeting_title)s.</p>
            <p>Start date: %(start_date_time)s</p>
            <p>Recurring until date: %(end_date)s</p>
            <p>The meeting will be occur each %(frequency)s %(recurrence)s </p>
            <p>Here is the link to join the meeting: %(join_link)s</p>
            <p>You need this password to enter: %(password)s</p>
            <p>Regards</p>
        """
            )
            % {
                "owner": full_name,
                "meeting_title": meeting.name,
                "start_date_time": meeting_start_datetime,
                "end_date": meeting.recurring_until.strftime("%d/%m/%Y"),
                "frequency": meeting.frequency,
                "recurrence": meeting.get_recurrence_display().lower(),
                "join_link": join_link,
                "password": meeting.attendee_password,
            }
        )
    else:
        html_content = (
            _(
                """
            <p>Hello,</p>
            <p>%(owner)s invites you to the meeting <b>%(meeting_title)s</b>.</p>
            <p>Start date: %(start_date_time)s </p>
            <p>End date: %(end_date)s </p>
            <p>here the link to join the meeting:
            <a href="%(join_link)s">%(join_link)s</a></p>
            <p>You need this password to enter: <b>%(password)s</b> </p>
            <p>Regards</p>
        """
            )
            % {
                "owner": full_name,
                "meeting_title": meeting.name,
                "start_date_time": meeting_start_datetime,
                "end_date": timezone.localtime(
                    meeting.start_at + meeting.expected_duration
                ).strftime("%d/%m/%Y %H:%M"),
                "join_link": join_link,
                "password": meeting.attendee_password,
            }
        )
    return html_content


def create_ics(request, meeting):
    join_link = request.build_absolute_uri(
        reverse("meeting:join", args=(meeting.meeting_id,))
    )
    event_name = _("%(owner)s invites you to the meeting %(meeting_title)s") % {
        "owner": meeting.owner.get_full_name(),
        "meeting_title": meeting.name,
    }
    description = (
        _(
            """
        Here is the link to join the meeting: %(join_link)s
        You need this password to enter: %(password)s
    """
        )
        % {"join_link": join_link, "password": meeting.attendee_password}
    )
    event_description = "\\n".join(
        line for line in description.replace("    ", "").split("\n")
    )

    start_date_time = 'TZID="%s":%s' % (
        timezone.get_current_timezone(),
        timezone.localtime(meeting.start_at).strftime("%Y%m%dT%H%M%S"),
    )

    duration = int(meeting.expected_duration.seconds / 3600)
    rrule = ""
    if meeting.recurrence:
        rrule = get_rrule(meeting)

    event = """
    BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:%(prodid)s
    BEGIN:VEVENT
    DESCRIPTION:%(description)s
    DURATION:PT%(duration)sH
    ORGANIZER;CN=%(mail)s:mailto:%(mail)s
    DTSTART;%(dtstart)s
    %(rrule)s
    SUMMARY:%(summary)s
    URL:%(url)s
    UID:%(uid)s
    BEGIN:VALARM
    ACTION:DISPLAY
    DESCRIPTION:%(summary)s
    TRIGGER:-PT5M
    END:VALARM
    END:VEVENT
    END:VCALENDAR
    """ % {
        "prodid": __TITLE_SITE__ + " - " + request.scheme + "://" + request.get_host(),
        "summary": event_name,
        "description": event_description,
        "duration": duration,
        "url": join_link,
        "mail": meeting.owner.email,
        "rrule": rrule,
        "dtstart": start_date_time,
        "uid": meeting.meeting_id + "@" + request.get_host(),
    }
    event_lines = event.replace("    ", "").split("\n")
    return "\n".join(filter(None, event_lines))


def get_rrule(meeting):
    """
    i.e:
    RRULE:FREQ=DAILY;INTERVAL=2;COUNT=28
    RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,TU;UNTIL=20221011T100000Z
    RRULE:FREQ=MONTHLY;BYDAY=1MO;COUNT=42
    RRULE:FREQ=MONTHLY;BYDAY=4TH;COUNT=42
    RRULE:FREQ=MONTHLY;BYMONTHDAY=3;UNTIL=20221024T100000Z
    """
    DAYS_OF_WEEK = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
    rrule = "RRULE:FREQ=%s;INTERVAL=%s;" % (meeting.recurrence.upper(), meeting.frequency)
    if meeting.recurrence == Meeting.WEEKLY:
        rrule += "BYDAY=%s;" % ",".join(
            DAYS_OF_WEEK[int(d)] for d in list(meeting.weekdays)
        )

    if meeting.recurrence == Meeting.MONTHLY:
        if meeting.monthly_type == Meeting.DATE_DAY:
            rrule += "BYMONTHDAY=%s;" % meeting.start.strftime("%d")
        if meeting.monthly_type == Meeting.NTH_DAY:
            weekday = meeting.start.weekday()
            week_number = get_nth_week_number(meeting.start)
            rrule += "BYDAY=%s%s;" % (week_number, DAYS_OF_WEEK[weekday])

    if meeting.nb_occurrences and meeting.nb_occurrences > 1:
        rrule += "COUNT=%s" % meeting.nb_occurrences
    else:
        end = datetime.combine(meeting.recurring_until, meeting.start_time)
        end_date_time = timezone.make_aware(end)
        rrule += "UNTIL=%s" % end_date_time.strftime("%Y%m%dT%H%M%S%z")
    return rrule


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def upload_internal_recording_to_pod(request, recording_id, meeting_id):
    """Upload internal recording to Pod.

    Args:
        request (Request): HTTP request
        recording_id (String): recording id (BBB format)
        meeting_id (String): meeting id (BBB format)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the recordings list
    """
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )
    # Secure the internal recordings
    secure_internal_recordings(request, meeting)

    # Only POST request
    secure_post_request(request)

    msg = ""
    upload = False
    try:
        # Save the internal recording, before the upload
        recording_title = request.POST.get("recording_name")
        save_internal_recording(request, recording_id, recording_title, meeting_id)
        # Get it
        recording = get_object_or_404(
            Recording,
            recording_id=recording_id,
            meeting_id=meeting.id,
            site=get_current_site(request),
            is_internal=True
        )

        # Upload this recording
        upload = upload_recording_to_pod(request, recording.id, meeting_id)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if (args.get('error')):
            msg += "<strong>%s</strong><br/>" % (args['error'])
        if (args.get('message')):
            msg += args['message']
        if (args.get('proposition')):
            msg += "<br/><span class='proposition'>%s</span>" % (args['proposition'])
    if upload and msg == "":
        msg += _(
            "The recording has been uploaded to Pod. "
            "You can see the generated video in My videos."
        )
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:internal_recordings", args=(meeting.meeting_id,)))


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def upload_external_recording_to_pod(request, record_id):
    """Upload external recording to Pod.

    Args:
        request (Request): HTTP request
        recording_id (Integer): record id (in database)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the external recordings list
    """
    recording = get_object_or_404(
        Recording, id=record_id, site=get_current_site(request)
    )

    # Secure this external recording
    secure_external_recording(request, recording)

    # Only POST request
    secure_post_request(request)

    msg = ""
    upload = False
    try:
        upload = upload_recording_to_pod(request, record_id)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if (args.get('error')):
            msg += "<strong>%s</strong><br/>" % (args['error'])
        if (args.get('message')):
            msg += args['message']
        if (args.get('proposition')):
            msg += "<br/><span class='proposition'>%s</span>" % (args['proposition'])
    if upload and msg == "":
        msg += _(
            "The recording has been uploaded to Pod. "
            "You can see the generated video in My videos."
        )
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:external_recordings", args=()))


@login_required(redirect_field_name="referrer")
def external_recordings(request):
    """List external recordings.

    Args:
        request (Request): HTTP Request

    Returns:
        HTTPResponse: external recordings list
    """
    # print(timezone.localtime().strftime("%y%m%d-%H%M%S"))

    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(
            request,
            "meeting/external_recordings.html",
            {"access_not_allowed": True}
        )

    site = get_current_site(request)

    # List of the external recordings from the database
    external_recordings = Recording.objects.filter(
        owner__id=request.user.id, is_internal=False, site=site
    ) | request.user.owners_recordings.all().filter(site=site)
    external_recordings = external_recordings.order_by("-id").distinct()

    recordings = []
    for data in external_recordings:
        # Management of the stateless recording
        recording = StatelessRecording(
            data.id, data.name, "published"
        )
        # Upload to Pod is always possible in such a case
        recording.canUpload = True
        # Only owner can delete this external recording
        recording.canDelete = get_can_delete_external_recording(request, data.owner)

        recording.startTime = data.start_at
        # recording.endTime = data.endTime

        # Management of the external recording type
        if data.type == "bigbluebutton":
            # For BBB, external URL can be the video or presentation playback
            if data.source_url.find("playback/video") != -1:
                # Management for standards video URLs with BBB or Scalelite server
                recording.videoUrl = data.source_url
            elif data.source_url.find("playback/presentation/2.3") != -1:
                # Management for standards presentation URLs with BBB or Scalelite server
                # Add computed video playback
                recording.videoUrl = data.source_url.replace(
                    "playback/presentation/2.3", "playback/video"
                )
            else:
                # Management of other situations, non standards URLs
                recording.videoUrl = data.source_url
        else:
            # For PeerTube, Video file, Youtube
            recording.videoUrl = data.source_url

        # Display type label
        recording.type = data.get_type_display

        recording.uploadedToPodBy = data.uploaded_to_pod_by

        recordings.append(recording)

    return render(
        request,
        "meeting/external_recordings.html",
        {
            "recordings": recordings,
            "page_title": _("External recordings"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def add_or_edit_external_recording(request, id=None):
    """Add or edit an external recording.

    Args:
        request (Request): HTTP request
        id (Integer, optional): external recording id. Defaults to None (for creation).

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTPResponse: edition page
    """
    if in_maintenance():
        return redirect(reverse("maintenance"))

    recording = (
        get_object_or_404(Recording, id=id, site=get_current_site(request))
        if id
        else None
    )

    # Secure external recording
    secure_external_recording(request, recording)

    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(
            request,
            "meeting/add_or_edit_external_recording.html",
            {"access_not_allowed": True}
        )

    default_owner = recording.owner.pk if recording else request.user.pk
    form = RecordingForm(
        instance=recording,
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": default_owner, "id": id},
    )

    if request.method == "POST":
        form = RecordingForm(
            request.POST,
            instance=recording,
            is_staff=request.user.is_staff,
            is_superuser=request.user.is_superuser,
            current_user=request.user,
            current_lang=request.LANGUAGE_CODE,
        )
        if form.is_valid():
            recording = save_recording_form(request, form)
            display_message_with_icon(
                request, messages.INFO, _("The changes have been saved.")
            )
            return redirect(reverse("meeting:external_recordings"))
        else:
            display_message_with_icon(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    page_title = (
        "%s <b>%s</b>" % (_("Edit the external recording"), recording.name)
        if recording
        else _("Add a new external recording")
    )
    return render(
        request,
        "meeting/add_or_edit_external_recording.html",
        {"form": form, "page_title": mark_safe(page_title)},
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def delete_external_recording(request, id):
    """Delete an external recording.

    Args:
        request (Request): HTTP request
        id (Integer): record id (in database)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTP Response: Redirect to the recordings list
    """
    recording = get_object_or_404(
        Recording, id=id, site=get_current_site(request)
    )

    # Secure external recording
    secure_external_recording(request, recording)

    # Only POST request
    secure_post_request(request)

    msg = ""
    delete = False
    try:
        delete = recording.delete()
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if (args['error']):
            msg += "<strong>%s</strong><br/>" % (args['error'])
        if (args['message']):
            msg += args['message']
    if delete and msg == "":
        msg += _("The external recording has been deleted.")
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:external_recordings", args=()))


def save_recording_form(request, form):
    """Save an external recording.

    Args:
        request (Request): HTTP request
        form (Form): recording form

    Returns:
        Recording: recording saved in database
    """
    recording = form.save(commit=False)
    recording.site = get_current_site(request)
    if (
        (request.user.is_superuser or request.user.has_perm("meeting.add_recording"))
        and request.POST.get("owner")
        and request.POST.get("owner") != ""
    ):
        recording.owner = form.cleaned_data["owner"]
    elif getattr(recording, "owner", None) is None:
        recording.owner = request.user

    recording.save()
    form.save_m2m()
    return recording


# ##############################    Upload recordings to Pod
def parse_remote_file(source_html_url):
    """Parse the remote HTML file on the BBB server.

    Args:
        source_html_url (String): URL to parse

    Raises:
        ValueError: exception raised if no video found in this URL

    Returns:
        String: name of the video found in the page
    """
    try:
        response = requests.get(source_html_url)
        if response.status_code != 200:
            msg = {}
            msg["error"] = _(
                "The HTML file for this recording was not found on the BBB server."
            )
            # If we want to display the 404/500... page to the user
            # msg["message"] = response.content.decode("utf-8")
            msg["message"] = "Error number : %s" % response.status_code
            raise ValueError(msg)

        # Parse the BBB video HTML file
        parser = video_parser()
        # Manage the encoding
        if response.encoding == "ISO-8859-1":
            parser.feed(response.text.encode("ISO-8859-1").decode("utf-8"))
        else:
            parser.feed(response.text)

        # Video file found
        if parser.video_check:
            # Security check about extensions
            extension = parser.video_file.split(".")[-1].lower()
            if extension not in VIDEO_ALLOWED_EXTENSIONS:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording was not "
                    "found in the HTML file."
                )
                msg["message"] = _("The found file is not a valid video.")
                raise ValueError(msg)

            # Returns the name of the video (if necessary, title is parser.title)
            return parser.video_file
        else:
            msg = {}
            msg["error"] = _(
                "The video file for this recording was not found in the HTML file."
            )
            msg["message"] = _("No video file found")
            raise ValueError(msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _(
            "The video file for this recording was not found in the HTML file."
        )
        msg["message"] = str(exc)
        raise ValueError(msg)


def download_video_file(source_video_url, dest_file):
    """Download BBB video file.

    Args:
        source_video_url (String): Video file URL
        dest_file (String): Destination file of the Pod video

    Raises:
        ValueError: if impossible download
    """
    # Check if video file exists
    try:
        with requests.get(
            source_video_url, timeout=(10, 180), stream=True
        ) as response:
            if response.status_code != 200:
                msg = {}
                msg["error"] = _(
                    "The video file for this recording "
                    "was not found on the BBB server."
                )
                # If we want to display the 404/500... page to the user
                # msg["message"] = response.content.decode("utf-8")
                msg["message"] = "Error number : %s" % response.status_code
                raise ValueError(msg)

            with open(dest_file, "wb+") as file:
                # Total size, in bytes, from response header
                # total_size = int(response.headers.get('content-length', 0))
                # Other possible methods
                # Method 1 : iterate over every chunk and calculate % of total
                # for chunk in response.iter_content(chunk_size=1024*1024):
                #    file.write(chunk)
                # Method 2 : Binary download
                # file.write(response.content)
                # Method 3 : The fastest
                shutil.copyfileobj(response.raw, file)
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to download the video file from the server.")
        msg["message"] = str(exc)
        raise ValueError(msg)


def save_video(
        request,
        dest_file,
        recording_name,
        description,
        recording,
        date_evt=None):
    """Save and encode the Pod video file.

    Args:
        request (Request): HTTP request
        dest_file (String): Destination file of the Pod video
        recording_name (String): recording name
        description (String): description added to the Pod video
        recording (Recording): Recording object
        date_evt (Datetime, optional): Event date. Defaults to None.

    Raises:
        ValueError: if impossible creation
    """
    try:
        video = Video.objects.create(
            video=dest_file,
            title=recording_name,
            owner=request.user,
            description=description,
            is_draft=True,
            type=Type.objects.get(id=DEFAULT_TYPE_ID),
            date_evt=date_evt,
        )
        for additional_owner in recording.additional_owners.all():
            video.additional_owners.add(additional_owner)

        video.launch_encode = True
        video.save()
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to create the Pod video")
        msg["message"] = str(exc)
        raise ValueError(msg)


def save_internal_recording(
        request,
        recording_id,
        recording_name,
        meeting_id,
        source_url=None):
    """Save an internal recording in database.

    Args:
        request (Request): HTTP request
        recording_id (String): recording id (BBB format)
        recording_name (String): recording name
        meeting_id (String): meeting id (BBB format)
        source_url (String, optional): Video file URL. Defaults to None.

    Raises:
        ValueError: if impossible creation
    """
    try:
        meeting = get_object_or_404(
            Meeting, meeting_id=meeting_id, site=get_current_site(request)
        )

        """ Useless for the moment
        # Convert timestamp to datetime
        start_timestamp = request.POST.get("start_timestamp")
        end_timestamp = request.POST.get("end_timestamp")
        start_dt = dt.fromtimestamp(float(start_timestamp) / 1000)
        end_dt = dt.fromtimestamp(float(end_timestamp) / 1000)
        # Format datetime and not timestamp
        start_at = start_dt.strftime("%Y-%m-%d %H:%M:%S")
        # Management of the duration
        duration = str(end_dt - start_dt).split(".")[0]
        """

        if (source_url is None):
            source_url = ""
        # Save the recording as an internal recording
        recording, created = Recording.objects.update_or_create(
            name=recording_name,
            is_internal=True,
            recording_id=recording_id,
            meeting=meeting,
            # start_at=start_at,
            # duration=parse_duration(duration),
            owner=meeting.owner,
            defaults={"uploaded_to_pod_by": request.user, "source_url": source_url},
        )
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to create the internal recording")
        msg["message"] = str(exc)
        raise ValueError(msg)


def save_external_recording(request, record_id):
    """Save an external recording in database.

    Args:
        request (Request): HTTP request
        record_id (Integer): id of the recording in database

    Raises:
        ValueError: if impossible creation
    """
    try:
        # Update the external recording
        recording, created = Recording.objects.update_or_create(
            id=record_id,
            is_internal=False,
            defaults={"uploaded_to_pod_by": request.user},
        )
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to create the external recording")
        msg["message"] = str(exc)
        raise ValueError(msg)


def upload_recording_to_pod(request, record_id, meeting_id=None):
    """Upload recording to Pod (main function).

    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database
        meeting_id (String, optional): meeting id (BBB format) for internal recording.

    Raises:
        ValueError: exception raised if no URL found or other problem

    Returns:
        Boolean: True if upload achieved
    """
    try:
        # Management by type of recording
        recording = Recording.objects.get(id=record_id)

        # Check that request is correct for upload
        secure_request_for_upload(request)

        # Manage differents source types
        if (recording.type == "youtube"):
            return upload_youtube_recording_to_pod(request, record_id)
        elif (recording.type == "peertube"):
            return upload_peertube_recording_to_pod(request, record_id)
        else:
            return upload_bbb_recording_to_pod(request, record_id, meeting_id)
    except Exception as exc:
        msg = {}
        proposition = ""
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
            proposition = exc.args[0].get('proposition')
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = proposition
        raise ValueError(msg)


def upload_bbb_recording_to_pod(request, record_id, meeting_id=None):
    """Upload a BBB or video file recording to Pod.

    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database
        meeting_id (String, optional): meeting id (BBB format) for internal recording.

    Raises:
        ValueError: exception raised if no video found at this URL

    Returns:
        Boolean: True if upload achieved
    """
    try:
        recording = Recording.objects.get(id=record_id)
        source_url = request.POST.get("source_url")

        # Step 1 : Download and parse the remote HTML file if necessary
        # Check if extension is a video extension
        extension = source_url.split(".")[-1].lower()
        if extension in VIDEO_ALLOWED_EXTENSIONS:
            # URL corresponds to a video file
            source_video_url = source_url
        else:
            # Download and parse the remote HTML file
            video_file = parse_remote_file(source_url)
            source_video_url = source_url + video_file

        # Step 2 : Define destination source file
        extension = source_video_url.split(".")[-1].lower()
        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, recording.id, extension)),
        )

        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        # Step 3 : Download the video file
        download_video_file(source_video_url, dest_file)

        # Step 4 : Save informations about the recording
        recording_title = request.POST.get("recording_name")
        if meeting_id is not None:
            save_internal_recording(
                request,
                recording.recording_id,
                recording_title,
                meeting_id,
                source_video_url
            )
        else:
            save_external_recording(request, record_id)

        # Step 5 : Save and encode Pod video
        description = _(
            "This video was uploaded to Pod; its origin is %(type)s : "
            "<a href=\"%(url)s\" target=\"_blank\">%(url)s</a>"
        ) % {
            "type": recording.get_type_display(),
            "url": source_video_url
        }

        save_video(request, dest_file, recording_title, description, recording)

        return True
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


def upload_youtube_recording_to_pod(request, record_id):
    """Upload Youtube recording to Pod.

    Use PyTube with its API
    More information : https://pytube.io/en/latest/api.html
    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no YouTube video found or content inaccessible

    Returns:
        Boolean: True if upload achieved
    """
    try:
        recording = Recording.objects.get(id=record_id)

        # Manage source URL from video playback
        source_url = request.POST.get("source_url")

        # Use pytube to download Youtube file
        yt_video = YouTube(
            source_url,
            # on_complete_callback=complete_func,
            # use_oauth=True,
            # allow_oauth_cache=True
        )
        # Publish date (format : 2023-05-13 00:00:00)
        # Event date (format : 2023-05-13)
        date_evt = str(yt_video.publish_date)[0:10]

        # Setting video resolution
        yt_stream = yt_video.streams.get_highest_resolution()

        # User directory
        dest_dir = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
        )
        os.makedirs(os.path.dirname(dest_dir), exist_ok=True)

        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = "%s-%s" % (discrim, yt_stream.default_filename)
        # Video file path
        dest_file = os.path.join(
            dest_dir,
            filename,
        )

        # Download video
        yt_stream.download(
            dest_dir,
            filename=filename
        )

        # Step 4 : Save informations about the recording
        save_external_recording(request, record_id)

        # Step 5 : Save and encode Pod video
        description = _(
            "This video '%(name)s' was uploaded to Pod; "
            "its origin is Youtube : <a href=\"%(url)s\" target=\"_blank\">%(url)s</a>"
        ) % {
            "name": yt_video.title,
            "url": source_url
        }
        recording_title = request.POST.get("recording_name")
        save_video(request, dest_file, recording_title, description, recording, date_evt)
        return True

    except VideoUnavailable:
        msg = {}
        msg["error"] = _("YouTube error")
        msg["message"] = _(
            "YouTube content is unavailable. "
            "This content does not appear to be publicly available."
        )
        msg["proposition"] = _(
            "Try changing the access rights to the video directly in Youtube."
        )
        raise ValueError(msg)
    except PytubeError:
        msg = {}
        msg["error"] = _("YouTube error")
        msg["message"] = _(
            "YouTube content is inaccessible. "
            "This content does not appear to be publicly available."
        )
        msg["proposition"] = _(
            "Try changing the address of this recording."
        )
        raise ValueError(msg)
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


def upload_peertube_recording_to_pod(request, record_id):  # noqa: C901
    """Upload Peertube recording to Pod.

    More information : https://docs.joinpeertube.org/api/rest-getting-started
    Args:
        request (Request): HTTP request
        record_id (Integer): id record in the database

    Raises:
        ValueError: exception raised if no PeerTube video found in this URL

    Returns:
        Boolean: True if upload achieved
    """
    try:
        recording = Recording.objects.get(id=record_id)

        # Manage source URL from video playback
        source_url = request.POST.get("source_url")

        # Check if extension is a video extension
        extension = source_url.split(".")[-1].lower()
        if extension in VIDEO_ALLOWED_EXTENSIONS:
            # URL corresponds to a video file. Format example :
            #  - https://xxxx.fr/download/videos/id-quality.mp4
            # with : id = id/uuid/shortUUID, quality=480/720/1080
            source_video_url = source_url
            # PeerTube API for this video :
            # https://xxxx.fr/api/v1/videos/id
            pos_pt = source_url.rfind("-")
            if pos_pt != -1:
                url_api_video = source_url[0:pos_pt].replace(
                    "/download/videos/",
                    "/api/v1/videos/"
                )
            else:
                msg = {}
                msg["error"] = _("PeerTube error")
                msg["message"] = _(
                    "The address entered does not appear to be a valid PeerTube address."
                )
                msg["proposition"] = _("Try changing the address of the recording.")
                raise ValueError(msg)
        else:
            # URL corresponds to a PeerTube URL. Format example :
            #  - https://xxx.fr/w/id
            #  - https://xxx.fr/videos/watch/id
            # with : id = id/uuid/shortUUID
            # PeerTube API for this video :
            # https://xxxx.fr/api/v1/videos/id
            url_api_video = source_url.replace("/w/", "/api/v1/videos/")
            url_api_video = url_api_video.replace("/videos/watch/", "/api/v1/videos/")

        with requests.get(
            url_api_video, timeout=(10, 180), stream=True
        ) as response:
            if response.status_code != 200:
                msg = {}
                msg["error"] = _("PeerTube error")
                msg["message"] = _(
                    "The address entered does not appear to be a valid PeerTube address "
                    "or the PeerTube server is not responding as expected."
                )
                msg["proposition"] = _(
                    "Try changing the address of the recording or retry later."
                )
                raise ValueError(msg)
            else:
                pt_video_json = json.loads(response.content.decode("utf-8"))
                # URL
                pt_video_url = pt_video_json['url']
                # UUID, useful for the filename
                pt_video_uuid = pt_video_json['uuid']
                pt_video_name = pt_video_json['name']
                pt_video_description = pt_video_json['description']
                if pt_video_description is None:
                    pt_video_description = ""
                else:
                    pt_video_description = pt_video_description.replace("\r\n", "<br/>")
                # Creation date (format : 2023-05-23T08:16:34.690Z)
                pt_video_created_at = pt_video_json['createdAt']
                # Evant date (format : 2023-05-23)
                date_evt = pt_video_created_at[0:10]
                # Source video file
                source_video_url = pt_video_json['files'][0]['fileDownloadUrl']

        # Step 2 : Define destination source file
        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        extension = source_video_url.split(".")[-1].lower()
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            "videos",
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, pt_video_uuid, extension)),
        )
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        # Step 3 : Download the video file
        download_video_file(source_video_url, dest_file)

        # Step 4 : Save informations about the recording
        recording_title = request.POST.get("recording_name")
        save_external_recording(request, record_id)

        # Step 5 : Save and encode Pod video
        description = _(
            "This video '%(name)s' was uploaded to Pod; its origin is PeerTube : "
            "<a href='%(url)s' target='blank'>%(url)s</a>."
        ) % {
            "name": pt_video_name,
            "url": pt_video_url
        }
        description = ("%s<br/>%s") % (description, pt_video_description)
        save_video(request, dest_file, recording_title, description, recording, date_evt)

        return True
    except Exception as exc:
        msg = {}
        msg["error"] = _("Impossible to upload to Pod the PeerTube video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = _(
            "Try changing the record type or address for this recording."
        )
        raise ValueError(msg)


class video_parser(HTMLParser):
    """Useful to parse the BBB Web page and search for video file.

    Used to parse BBB 2.6+ URL for video recordings.
    Args:
        HTMLParser (_type_): _description_
    """

    def __init__(self):
        super().__init__()
        self.reset()
        # Variables for title
        self.title_check = False
        self.title = ""
        # Variables for video file
        self.video_check = False
        self.video_file = ""
        self.video_type = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Search for source tag
        if tag == "source":
            # Found the line. Managed format :
            # attrs = {'src': 'video-0.m4v', 'type': 'video/mp4'}
            # print("video line : %s" % attrs)
            self.video_check = True
            self.video_file = attrs.get("src", "")
            self.video_type = attrs.get("type", "")
        # Search for title tag
        if tag == "title":
            # Found the title line
            self.title_check = True

    def handle_data(self, data):
        # Search for title tag
        if self.title_check:
            # Get the title that corresponds to recording's name
            self.title = data
            self.title_check = False
