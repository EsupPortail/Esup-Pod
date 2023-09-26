"""Views of the Meeting module."""
import bleach
import jwt
import logging
import os
import requests
import traceback

from .forms import MeetingForm, MeetingDeleteForm, MeetingPasswordForm
from .forms import MeetingInviteForm
from .models import Meeting, InternalRecording
from .utils import get_nth_week_number, send_email_recording_ready
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import SuspiciousOperation
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from pod.import_video.utils import StatelessRecording
from pod.import_video.utils import manage_download, parse_remote_file
from pod.import_video.utils import save_video, secure_request_for_upload
from pod.main.views import in_maintenance, TEMPLATE_VISIBLE_SETTINGS
from pod.main.utils import secure_post_request, display_message_with_icon

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
BBB_SECRET_KEY = getattr(settings, "BBB_SECRET_KEY", "")
MEETING_DISABLE_RECORD = getattr(settings, "MEETING_DISABLE_RECORD", True)

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

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)

log = logging.getLogger(__name__)


@login_required(redirect_field_name="referrer")
def my_meetings(request):
    """List the meetings."""
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
    """Add or edit a meeting."""
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
    start_date_formats = '["%s"]' % '","'.join(form.fields["start"].input_formats)
    return render(
        request,
        "meeting/add_or_edit.html",
        {
            "form": form,
            "start_date_formats": start_date_formats,
            "page_title": mark_safe(page_title),
        },
    )


def save_meeting_form(request, form):
    """Save a meeting form."""
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
    """Delete a meeting."""
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
    """Join a meeting."""
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
    """Render show page."""
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
    """Join as a moderator."""
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
            msg += "<b>%s:</b> %s<br>" % (key, args[key])
        display_message_with_icon(request, messages.ERROR, mark_safe(msg))
        return render(
            request,
            "meeting/join.html",
            {"meeting": meeting, "form": None},
        )


def check_user(request):
    """Check user."""
    if request.user.is_authenticated:
        display_message_with_icon(
            request, messages.ERROR, _("You cannot access to this meeting.")
        )
        raise PermissionDenied
    else:
        return redirect("%s?referrer=%s" % (settings.LOGIN_URL, request.get_full_path()))


def check_form(request, meeting, remove_password_in_form):
    """Check form."""
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
    """Return if user in the meeting."""
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
    """Status of a meeting, in JSON format."""
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
    """End meeting, in JSON format.."""
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
    """Get meeting info, in JSON format."""
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
def get_internal_recordings(request, meeting_id, recording_id=None):
    """List the internal recordings, depends on parameters (core function).

    Args:
        request (Request): HTTP request
        meeting_id (String): meeting id (BBB format)
        recording_id (String, optional): recording id (BBB format)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        recordings[]: Array of recordings corresponding to parameters
    """
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )

    # Secure the list of internal recordings
    secure_internal_recordings(request, meeting)

    # The user can delete this recording ?
    can_delete = get_can_delete_recordings(request, meeting)

    # Get one or more recordings
    meeting_recordings = get_one_or_more_recordings(request, meeting, recording_id)

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
            recording = InternalRecording.objects.filter(
                recording_id=data["recordID"]
            ).first()
            if recording:
                bbb_recording.uploadedToPodBy = recording.uploaded_to_pod_by
            recordings.append(bbb_recording)

    return recordings


@login_required(redirect_field_name="referrer")
def get_one_or_more_recordings(request, meeting, recording_id=None):
    """Define recordings useful for get_internal_recordings function."""
    if recording_id is None:
        meeting_recordings = meeting.get_recordings()
    else:
        meeting_recordings = meeting.get_recording(recording_id)
    return meeting_recordings


@login_required(redirect_field_name="referrer")
def internal_recordings(request, meeting_id):
    """List the internal recordings (main function).

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
    # Call the core function
    recordings = get_internal_recordings(request, meeting_id)

    return render(
        request,
        "meeting/internal_recordings.html",
        {
            "meeting": meeting,
            "recordings": recordings,
            "page_title": _("Meeting recordings"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def internal_recording(request, meeting_id, recording_id):
    """Get an internal recording, in JSON format (main function).

    Args:
        request (Request): HTTP request
        meeting_id (String): meeting id (BBB format)
        recording_id (String): recording id (BBB format)

    Raises:
        PermissionDenied: if user not allowed

    Returns:
        HTTPResponse: internal recording (JSON format)
    """
    # Call the core function
    recordings = get_internal_recordings(request, meeting_id, recording_id)
    # JSON format
    data = recordings[0].to_json()
    if request.is_ajax():
        return HttpResponse(data, content_type="application/json")
    else:
        return HttpResponseBadRequest()


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
    ):
        display_message_with_icon(
            request, messages.ERROR, _("You cannot view the recordings of this meeting.")
        )
        raise PermissionDenied


def get_can_delete_recordings(request, meeting):
    """Check if user can delete, or not, a recording of this meeting.

    Args:
        request (Request): HTTP request
        meeting (Meeting): Meeting instance

    Returns:
        Boolean: True if current user can delete the recordings of this meeting.
    """
    can_delete = False

    if (
        request.user == meeting.owner
        or (request.user.is_superuser)
        or (request.user.has_perm("meeting.delete_meeting"))
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
            msg += "<b>%s:</b> %s<br>" % (key, args[key])
        msg = mark_safe(msg)
    if delete and msg == "":
        display_message_with_icon(
            request, messages.INFO, _("The recording has been deleted.")
        )
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:internal_recordings", args=(meeting.meeting_id,)))


def get_meeting_info_json(info):
    """Get meeting info in JSON format."""
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
    """End the BBB callback."""
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
    """Invite users to a BBB meeting."""
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
    """Recipient emails."""
    emails = form.cleaned_data["emails"]
    if form.cleaned_data["owner_copy"] is True:
        emails.append(meeting.owner.email)
        for add_owner in meeting.additional_owners.all():
            emails.append(add_owner.email)
    return emails


def send_invite(request, meeting, emails):
    """Send invitations to users."""
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
    """Get HTML format content."""
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
    """Create ICS format."""
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
    """Get recurrence rule.

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


def get_video_url(request, meeting_id, recording_id):
    """Get recording video URL."""
    meeting = get_object_or_404(
        Meeting, meeting_id=meeting_id, site=get_current_site(request)
    )
    meeting_recordings = meeting.get_recording(recording_id)
    if type(meeting_recordings.get("recordings")) is dict:
        for data in meeting_recordings["recordings"].values():
            for playback in data["playback"]:
                # Uploading to Pod is possible only for video playback
                if data["playback"][playback]["type"] == "video":
                    source_url = data["playback"][playback]["url"]
    return source_url


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
            InternalRecording,
            recording_id=recording_id,
            meeting_id=meeting.id,
            site=get_current_site(request),
        )

        # Upload this recording
        upload = upload_recording_to_pod(request, recording.id, meeting_id)
    except ValueError as ve:
        args = ve.args[0]
        msg = ""
        if args.get("error"):
            msg += "<strong>%s</strong><br>" % (args["error"])
        if args.get("message"):
            msg += args["message"]
        if args.get("proposition"):
            msg += "<br><span class='proposition'>%s</span>" % (args["proposition"])
    if upload and msg == "":
        msg += _(
            "The recording has been uploaded to Pod. "
            "You can see the generated video in My videos."
        )
        display_message_with_icon(request, messages.INFO, msg)
    else:
        display_message_with_icon(request, messages.ERROR, msg)
    return redirect(reverse("meeting:internal_recordings", args=(meeting.meeting_id,)))


# ##############################    Upload recordings to Pod
def save_internal_recording(
    request, recording_id, recording_name, meeting_id, source_url=None
):
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

        if source_url is None:
            source_url = ""
        # Save the recording as an internal recording
        recording, created = InternalRecording.objects.update_or_create(
            name=recording_name,
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
        # Check that request is correct for upload
        secure_request_for_upload(request)

        return upload_bbb_recording_to_pod(request, record_id, meeting_id)
    except Exception as exc:
        msg = {}
        proposition = ""
        msg["error"] = _("Impossible to upload to Pod the video")
        try:
            # Management of error messages from sub-functions
            message = "%s (%s)" % (exc.args[0]["error"], exc.args[0]["message"])
            proposition = exc.args[0].get("proposition")
        except Exception:
            # Management of error messages in all cases
            message = str(exc)

        msg["message"] = mark_safe(message)
        msg["proposition"] = proposition
        raise ValueError(msg)


def upload_bbb_recording_to_pod(request, record_id, meeting_id):
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
        # Session useful to achieve requests (and keep cookies between)
        session = requests.Session()

        recording = InternalRecording.objects.get(id=record_id)

        source_url = get_video_url(request, meeting_id, recording.recording_id)

        # Step 1: Download and parse the remote HTML file if necessary
        # Check if extension is a video extension
        extension = source_url.split(".")[-1].lower()
        # Name of the video file to add to the URL (if necessary)
        video_file_add = ""
        if extension not in VIDEO_ALLOWED_EXTENSIONS:
            # Download and parse the remote HTML file
            video_file_add = parse_remote_file(session, source_url)
            # Extension overload
            extension = video_file_add.split(".")[-1].lower()

        # Step 2: Define destination source file
        discrim = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_file = os.path.join(
            settings.MEDIA_ROOT,
            VIDEOS_DIR,
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, recording.id, extension)),
        )
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)

        dest_path = os.path.join(
            VIDEOS_DIR,
            request.user.owner.hashkey,
            os.path.basename("%s-%s.%s" % (discrim, recording.id, extension)),
        )

        # Step 3: Download the video file
        source_video_url = manage_download(session, source_url, video_file_add, dest_file)

        # Step 4: Save informations about the recording
        recording_title = request.POST.get("recording_name")
        save_internal_recording(
            request,
            recording.recording_id,
            recording_title,
            meeting_id,
            source_video_url,
        )

        # Step 5: Save and encode Pod video
        description = _(
            "This video was uploaded to Pod; its origin is %(type)s: "
            '<a href="%(url)s" target="_blank">%(url)s</a>'
        ) % {"type": "Big Blue Button", "url": source_video_url}

        save_video(request, dest_path, recording_title, description)

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


@csrf_exempt
def recording_ready(request):
    """Make a callback when a recording is ready for viewing.

    Useful to send an email to prevent the user.
    See https://docs.bigbluebutton.org/development/api/#recording-ready-callback-url
    Args:
        request (Request): HTTP request

    Returns:
        HttpResponse: empty response
    """
    meeting_id = ""
    recording_id = ""
    try:
        if request.method == "POST":
            # Get parameters, encoded in HS256
            signed_parameters = request.POST.get("signed_parameters")
            # Decoded parameters with BBB secret key
            # Returns JSON format like : {'meeting_id': 'xxx', 'record_id': 'xxx'}
            decoded_parameters = jwt.decode(
                signed_parameters, BBB_SECRET_KEY, algorithms=["HS256"]
            )
            # Get data
            meeting_id = decoded_parameters["meeting_id"]
            recording_id = decoded_parameters["record_id"]
            meeting = get_object_or_404(
                Meeting, meeting_id=meeting_id, site=get_current_site(request)
            )
            # Send email to the owner
            send_email_recording_ready(meeting)
        else:
            raise ValueError("No POST method")

        return HttpResponse()
    except Exception as exc:
        log.error(
            "Error when check for recording (%s %s) ready URL: %s. %s"
            % (meeting_id, recording_id, mark_safe(str(exc)), traceback.format_exc())
        )
        return HttpResponse()
