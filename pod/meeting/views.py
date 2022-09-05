import os

from django.shortcuts import render

from django.http import JsonResponse, HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.utils.html import mark_safe
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from ics import Calendar, Event  # At the top of your .py file
from .models import Meeting
from .forms import MeetingForm, MeetingDeleteForm, MeetingPasswordForm, MeetingInviteForm
from pod.main.views import in_maintenance

RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = getattr(
    settings, "RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY", False
)
DEFAULT_FROM_EMAIL = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@univ.fr")
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


@login_required(redirect_field_name="referrer")
def my_meetings(request):
    site = get_current_site(request)
    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "meeting/my_meetings.html", {"access_not_allowed": True})
    meetings = request.user.owner_meeting.all().filter(site=site)
    return render(
        request,
        "meeting/my_meetings.html",
        {"meetings": meetings, "page_title": _("My meetings")},
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
        messages.add_message(request, messages.ERROR, _("You cannot edit this meeting."))
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
            messages.add_message(
                request, messages.INFO, _("The changes have been saved.")
            )
            return redirect(reverse("meeting:my_meetings"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )
    return render(
        request,
        "meeting/add_or_edit.html",
        {
            "form": form,
        },
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
        messages.add_message(
            request, messages.ERROR, _("You cannot delete this meeting.")
        )
        raise PermissionDenied

    form = MeetingDeleteForm()

    if request.method == "POST":
        form = MeetingDeleteForm(request.POST)
        if form.is_valid():
            meeting.delete()
            messages.add_message(
                request, messages.INFO, _("The meeting has been deleted.")
            )
            return redirect(reverse("meeting:my_meetings"))
        else:
            messages.add_message(
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
    # messages.add_message(request, messages.INFO, _("Join as moderator !"))
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
            messages.add_message(request, messages.ERROR, msg)
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
        messages.add_message(request, messages.ERROR, mark_safe(msg))
        return render(
            request,
            "meeting/join.html",
            {"meeting": meeting, "form": None},
        )


def check_user(request):
    if request.user.is_authenticated:
        messages.add_message(
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
                # messages.add_message(
                #     request, messages.INFO, _("Join as attendee !")
                # )
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
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Password given is not correct."),
                )
        else:
            messages.add_message(
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
        messages.add_message(
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
            msg += "<b>%s:</b> %s<br/>" % (key, args[key])
        msg = mark_safe(msg)
    if request.is_ajax():
        return JsonResponse({"end": meeting.end(), "msg": msg}, safe=False)
    else:
        if msg != "":
            messages.add_message(request, messages.ERROR, msg)
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
        messages.add_message(
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
            msg += "<b>%s:</b> %s<br/>" % (key, args[key])
        msg = mark_safe(msg)
    if request.is_ajax():
        return JsonResponse({"info": info, "msg": msg}, safe=False)
    else:
        if msg != "":
            messages.add_message(request, messages.ERROR, msg)
        return JsonResponse({"info": info, "msg": msg}, safe=False)


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
        messages.add_message(
            request, messages.ERROR, _("You cannot invite for this meeting.")
        )
        raise PermissionDenied
    form = MeetingInviteForm()
    if request.method == "POST":
        form = MeetingInviteForm(request.POST)

        if form.is_valid():
            emails = form.cleaned_data["emails"]
            send_invite(request, meeting, emails)
            messages.add_message(
                request, messages.INFO, _("Invitations send to recipients.")
            )
            return redirect(reverse("meeting:my_meetings"))
    return render(
        request,
        "meeting/invite.html",
        {"meeting": meeting, "form": form},
    )


def send_invite(request, meeting, emails):
    subject = _("%(owner)s invites you to the meeting %(meeting_title)s") % {
        "owner": meeting.owner.get_full_name(),
        "meeting_title": meeting.name,
    }
    from_email = meeting.owner.email  # DEFAULT_FROM_EMAIL
    join_link = request.build_absolute_uri(
        reverse("meeting:join", args=(meeting.meeting_id,))
    )
    text_content = (
        _(
            """
        Hello,
        %(owner)s invites you to the meeting %(meeting_title)s.
        Start date: %(start_date)s
        End date: %(end_date)s
        Here is the link to join the meeting: %(join_link)s
        You need this password to enter: %(password)s
        Regards
    """
        )
        % {
            "owner": meeting.owner.get_full_name(),
            "meeting_title": meeting.name,
            "start_date": meeting.start_at,
            "end_date": meeting.end_at,
            "join_link": join_link,
            "password": meeting.attendee_password,
        }
    )
    html_content = (
        _(
            """
        <p>Hello,
        <p>%(owner)s invites you to the meeting <b>%(meeting_title)s</b>.</p>
        <p>Start date: %(start_date)s </p>
        <p>End date: %(end_date)s </p>
        <p>here the link to join the meeting:
        <a href="%(join_link)s">%(join_link)s</a></p>
        <p>You need this password to enter: <b>%(password)s</b> </p>
        <p>Regards</p>
    """
        )
        % {
            "owner": meeting.owner.get_full_name(),
            "meeting_title": meeting.name,
            "start_date": meeting.start_at,
            "end_date": meeting.end_at,
            "join_link": join_link,
            "password": meeting.attendee_password,
        }
    )
    msg = EmailMultiAlternatives(subject, text_content, from_email, emails)
    msg.attach_alternative(html_content, "text/html")
    # ics calendar
    calendar = Calendar()
    event = Event()
    event.name = _("%(owner)s invites you to the meeting %(meeting_title)s") % {
        "owner": meeting.owner.get_full_name(),
        "meeting_title": meeting.name,
    }
    event.description = (
        _(
            """
        Here is the link to join the meeting: %(join_link)s
        You need this password to enter: %(password)s
    """
        )
        % {"join_link": join_link, "password": meeting.attendee_password}
    )
    event.begin = meeting.start_at
    event.end = meeting.end_at
    event.organizer = meeting.owner.email
    calendar.events.add(event)
    filename_event = "/tmp/invite-%d.ics" % meeting.id
    with open(filename_event, "w") as ics_file:
        ics_file.writelines(calendar)
    msg.attach_file(filename_event, "text/calendar")
    msg.send()
    os.remove(filename_event)
