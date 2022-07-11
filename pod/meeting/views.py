from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext_lazy as _


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
