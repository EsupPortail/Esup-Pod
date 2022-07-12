from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Meeting
from .forms import MeetingForm, MeetingDeleteForm
from pod.main.views import in_maintenance

RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = False


@login_required(redirect_field_name="referrer")
def my_meetings(request):
    site = get_current_site(request)
    meetings = request.user.owner_meeting.all().filter(
        site=site
    )
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
            not (request.user.is_superuser or request.user.has_perm("meeting.change_meeting"))
        )
        and (request.user not in meeting.additional_owners.all())
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this video."))
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
        {"form": form, },
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
    meeting = get_object_or_404(Meeting, meeting_id=meeting_id, site=get_current_site(request))

    if request.user != meeting.owner and not (
        request.user.is_superuser or request.user.has_perm("meeting.delete_meeting")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot delete this meeting."))
        raise PermissionDenied

    form = MeetingDeleteForm()

    if request.method == "POST":
        form = MeetingDeleteForm(request.POST)
        if form.is_valid():
            meeting.delete()
            messages.add_message(request, messages.INFO, _("The meeting has been deleted."))
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
def join(request, meeting_id):
    try:
        id = int(meeting_id[: meeting_id.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid video id")
    meeting = get_object_or_404(Meeting, id=id, site=get_current_site(request))

    return render(
        request,
        "meeting/join.html",
        {"meeting": meeting, },
    )
