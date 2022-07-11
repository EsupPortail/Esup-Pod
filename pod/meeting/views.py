from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_protect

from .models import Meeting


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


@login_required(redirect_field_name="referrer")
def add(request):
    # site = get_current_site(request)

    return HttpResponse("Hello, world. You're at the meeting index.")


@csrf_protect
def join(request, meeting_id):
    try:
        id = int(meeting_id[: meeting_id.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid video id")
    meeting = get_object_or_404(Meeting, id=id, sites=get_current_site(request))
    return render(
        request,
        "meeting/join.html",
        {"meeting": meeting, },
    )
