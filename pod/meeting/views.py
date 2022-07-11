from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from .models import Meeting
from .forms import MeetingForm

RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY = False


def index(request):
    return HttpResponse("Hello, world. You're at the meeting index.")


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
@login_required(redirect_field_name="referrer")
def add(request):
    """
    if request.user not in channel.owners.all() and not (
        request.user.is_superuser or request.user.has_perm("video.change_channel")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot edit this channel."))
        raise PermissionDenied
    """
    if RESTRICT_EDIT_MEETING_ACCESS_TO_STAFF_ONLY and request.user.is_staff is False:
        return render(request, "meeting/add.html", {"access_not_allowed": True})
    form = MeetingForm(
        is_staff=request.user.is_staff,
        is_superuser=request.user.is_superuser,
        current_user=request.user,
        initial={"owner": request.user},
    )
    return render(
        request,
        "meeting/add.html",
        {"form": form, },
    )


@csrf_protect
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
