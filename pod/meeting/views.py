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
    # Videos list which user is the owner + which user is an additional owner
    meetings_list = request.user.meeting_set.all().filter(
        sites=site
    )  # | request.user.owners_videos.all().filter(sites=site)
    meetings_list = meetings_list.distinct()
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
        meetings = paginator.page(page)
    except PageNotAnInteger:
        meetings = paginator.page(1)
    except EmptyPage:
        meetings = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(
            request,
            "meetings/meetings_list.html",
            {"videos": meetings, "full_path": full_path},
        )
    data_context = {}
    data_context["meetings"] = meetings
    data_context["full_path"] = full_path
    data_context["page_title"] = _("My meetings")

    return render(request, "meetings/my_meetings.html", data_context)
