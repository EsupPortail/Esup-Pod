import json
import logging
import os.path
import re
import threading
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Prefetch
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    JsonResponse,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
)
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from rest_framework import status

from pod.bbb.models import Livestream
from .forms import EventPasswordForm, EventForm, EventDeleteForm, EventImmediateForm
from .models import (
    Building,
    Broadcaster,
    HeartBeat,
    Event,
    get_available_broadcasters_of_building,
)
from .pilotingInterface import get_piloting_implementation
from .utils import (
    send_email_confirmation,
    get_event_id_and_broadcaster_id,
    check_exists,
    check_size_not_changing,
    check_permission,
)
from ..main.utils import is_ajax
from ..main.views import in_maintenance
from ..video.models import Video

HEARTBEAT_DELAY = getattr(settings, "HEARTBEAT_DELAY", 45)

USE_BBB = getattr(settings, "USE_BBB", False)
USE_BBB_LIVE = getattr(settings, "USE_BBB_LIVE", False)

DEFAULT_EVENT_PATH = getattr(settings, "DEFAULT_EVENT_PATH", "")
DEFAULT_EVENT_THUMBNAIL = getattr(
    settings, "DEFAULT_EVENT_THUMBNAIL", "/img/default-event.svg"
)
AFFILIATION_EVENT = getattr(
    settings, "AFFILIATION_EVENT", ("faculty", "employee", "staff")
)
EVENT_GROUP_ADMIN = getattr(settings, "EVENT_GROUP_ADMIN", "event admin")
VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")

logger = logging.getLogger("pod.live")

EMAIL_ON_EVENT_SCHEDULING = getattr(settings, "EMAIL_ON_EVENT_SCHEDULING", False)


@login_required(redirect_field_name="referrer")
def directs_all(request):  # affichage des directs
    check_permission(request)

    site = get_current_site(request)
    buildings = (
        Building.objects.all()
        .filter(sites=site)
        .prefetch_related(
            Prefetch(
                "broadcaster_set",
                queryset=Broadcaster.objects.filter(public=True),
            )
        )
    )
    return render(
        request,
        "live/directs_all.html",
        {
            "buildings": buildings,
        },
    )


@login_required(redirect_field_name="referrer")
def directs(request, building_id):  # affichage des directs d'un batiment
    check_permission(request)
    building = get_object_or_404(Building, id=building_id)
    return render(
        request,
        "live/directs.html",
        {"building": building},
    )


@login_required(redirect_field_name="referrer")
def direct(request, slug):  # affichage du flux d'un diffuseur
    check_permission(request)

    site = get_current_site(request)
    broadcaster = get_broadcaster_by_slug(slug, site)
    if broadcaster.is_restricted and not request.user.is_authenticated:
        iframe_param = "is_iframe=true&" if (request.GET.get("is_iframe")) else ""
        return redirect(
            "%s?%sreferrer=%s"
            % (settings.LOGIN_URL, iframe_param, request.get_full_path())
        )
    # Search if broadcaster is used to display a BBB streaming live
    # for which students can send message from this live page
    display_chat = False
    if USE_BBB and USE_BBB_LIVE:
        livestreams_list = Livestream.objects.filter(broadcaster_id=broadcaster.id)
        for livestream in livestreams_list:
            display_chat = livestream.enable_chat
    return render(
        request,
        "live/direct.html",
        {
            "display_chat": display_chat,
            "display_event_btn": can_manage_event(request.user),
            "broadcaster": broadcaster,
            "heartbeat_delay": HEARTBEAT_DELAY,
        },
    )


def get_broadcaster_by_slug(slug, site):
    if type(slug) == int:
        return get_object_or_404(Broadcaster, id=slug, building__sites=site)
    else:
        return get_object_or_404(Broadcaster, slug=slug, building__sites=site)


"""use rest api to change status
def change_status(request, slug):
    broadcaster = get_object_or_404(Broadcaster, slug=slug)
    if request.GET.get("online") == "1":
        broadcaster.status = 1
    else:
        broadcaster.status = 0
    broadcaster.save()
    return HttpResponse("ok")
"""


def heartbeat(request):
    if is_ajax(request) and request.method == "GET":
        broadcasterid = request.GET.get("broadcasterid")
        eventid = request.GET.get("eventid")
        if broadcasterid is None and eventid is None:
            return HttpResponse(
                content="missing parameters", status=status.HTTP_400_BAD_REQUEST
            )

        return manage_heartbeat(
            broadcasterid, eventid, request.GET.get("key", ""), request.user
        )

    return HttpResponseBadRequest()


def manage_heartbeat(broadcaster_id, event_id, key, current_user):
    mimetype = "application/json"
    current_event = None

    # Admin's supervision only
    if broadcaster_id is not None:
        # find current event with broadcaster id
        Event.objects.filter()
        query = Event.objects.filter(broadcaster_id=broadcaster_id)
        ids = [evt.id for evt in query if evt.is_current()]

        # no current event
        if len(ids) != 1:
            return HttpResponse(
                json.dumps(
                    {
                        "viewers": 0,
                        "viewers_list": [],
                    }
                ),
                mimetype,
            )

        current_event = get_object_or_404(Event, id=ids[0])

    # save viewer's heartbeat
    if event_id is not None:
        current_event = get_object_or_404(Event, id=event_id)
        viewer_heartbeat, created = HeartBeat.objects.get_or_create(
            viewkey=key, event_id=event_id
        )
        if created and not current_user.is_anonymous:
            viewer_heartbeat.user = current_user
        viewer_heartbeat.last_heartbeat = timezone.now()
        viewer_heartbeat.save()

    viewers = current_event.viewers.values("first_name", "last_name", "is_superuser")

    can_see = (
        current_user.is_superuser
        or current_user == current_event.owner
        or current_user in current_event.additional_owners.all()
    )

    heartbeats_count = HeartBeat.objects.filter(event_id=current_event.id).count()

    if current_event.max_viewers < heartbeats_count:
        current_event.max_viewers = heartbeats_count
        current_event.save()

    return HttpResponse(
        json.dumps(
            {
                "viewers": heartbeats_count,
                "viewers_list": list(viewers) if can_see else [],
            }
        ),
        mimetype,
    )


def can_manage_event(user):
    return user.is_authenticated and (
        user.is_superuser
        or user.owner.accessgroup_set.filter(code_name__in=AFFILIATION_EVENT).exists()
        or user.groups.filter(name=EVENT_GROUP_ADMIN).exists()
    )


def is_in_event_groups(user, evt):
    return user.owner.accessgroup_set.filter(
        code_name__in=[
            name[0] for name in evt.restrict_access_to_groups.values_list("code_name")
        ]
    ).exists()


def get_event_access(request, evt, slug_private, is_owner):
    """Return True if access is granted to current user."""

    if is_owner:
        return True

    if evt.is_draft:
        if slug_private or slug_private == evt.get_hashkey():
            can_access_draft = True
        else:
            can_access_draft = (
                request.user == evt.owner
                or request.user in evt.additional_owners.all()
                or request.user.is_superuser
            )
        if not can_access_draft:
            return False

    if evt.is_restricted and not request.user.is_authenticated:
        return False

    if evt.restrict_access_to_groups.all().exists() and (
        not request.user.is_authenticated or not is_in_event_groups(request.user, evt)
    ):
        return False

    return True


def event(request, slug, slug_private=None):  # affichage d'un event
    # modif de l'url d'appel pour compatibilité
    # avec le template link_video.html (variable: urleditapp)
    request.resolver_match.namespace = ""

    try:
        event_id = int(slug[: slug.find("-")])
    except ValueError:
        raise SuspiciousOperation("Invalid event id")

    evemnt = get_object_or_404(Event, id=event_id)

    if (
        evemnt.is_restricted or evemnt.restrict_access_to_groups.all().exists()
    ) and not request.user.is_authenticated:
        iframe_param = "is_iframe=true&" if (request.GET.get("is_iframe")) else ""
        return redirect(
            "%s?%sreferrer=%s"
            % (settings.LOGIN_URL, iframe_param, request.get_full_path())
        )

    user_owns_event = request.user.is_authenticated and (
        evemnt.owner == request.user
        or request.user in evemnt.additional_owners.all()
        or request.user.is_superuser
    )

    if not get_event_access(request, evemnt, slug_private, user_owns_event):
        messages.add_message(request, messages.ERROR, _("You cannot watch this event."))
        raise PermissionDenied

    return render_event_template(request, evemnt, user_owns_event)


def render_event_template(request, evemnt, user_owns_event):
    is_password_protected = evemnt.password is not None and evemnt.password != ""
    password_provided = request.POST.get("password") is not None
    password_correct = request.POST.get("password") == evemnt.password
    template_event = (
        "live/event-iframe.html" if request.GET.get("is_iframe") else "live/event.html"
    )

    # password protection
    if is_password_protected and not user_owns_event and not password_correct:
        form = EventPasswordForm(request.POST) if request.POST else EventPasswordForm()
        if password_provided:
            messages.add_message(request, messages.ERROR, _("The password is incorrect."))
        return render(
            request,
            template_event,
            {
                "event": evemnt,
                "form": form,
            },
        )

    # Search if broadcaster is used to display a BBB streaming live
    # for which students can send message from this live page
    display_chat = False
    if USE_BBB and USE_BBB_LIVE:
        livestreams_list = Livestream.objects.filter(broadcaster_id=evemnt.broadcaster_id)
        for livestream in livestreams_list:
            display_chat = livestream.enable_chat

    return render(
        request,
        template_event,
        {
            "event": evemnt,
            "display_chat": display_chat,
            "can_record": (
                user_owns_event
                and evemnt.broadcaster.piloting_implementation
                and not request.GET.get("is_iframe")
            ),
            "use_split": use_split(evemnt.broadcaster),
            "can_manage_stream": can_manage_stream(evemnt.broadcaster),
            "heartbeat_delay": HEARTBEAT_DELAY,
        },
    )


def events(request):
    """Affichage des events."""
    # Tous les events à venir (sauf les drafts sont affichés)
    queryset = Event.objects.filter(end_date__gt=timezone.now(), is_draft=False)
    events_list = queryset.all().order_by("start_date", "end_date")

    page = request.GET.get("page", 1)
    full_path = ""
    if page:
        full_path = (
            request.get_full_path()
            .replace("?page=%s" % page, "")
            .replace("&page=%s" % page, "")
        )

    paginator = Paginator(events_list, 12)
    try:
        events_found = paginator.page(page)
    except PageNotAnInteger:
        events_found = paginator.page(1)
    except EmptyPage:
        events_found = paginator.page(paginator.num_pages)

    return render(
        request,
        "live/events.html",
        {
            "events": events_found,
            "full_path": full_path,
            "DEFAULT_EVENT_THUMBNAIL": DEFAULT_EVENT_THUMBNAIL,
            "display_broadcaster_name": False,
            "display_direct_button": request.user.is_superuser
            or request.user.has_perm("live.acces_live_pages"),
            "display_creation_button": can_manage_event(request.user),
            "page_title": _("Events"),
        },
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def my_events(request):
    queryset = (
        request.user.event_set.all().distinct()
        | request.user.owners_events.all().distinct()
    )

    past_events = [evt for evt in queryset if evt.is_past()]
    past_events = sorted(past_events, key=lambda evt: evt.start_date, reverse=True)

    coming_events = [evt for evt in queryset if not evt.is_past()]
    coming_events = sorted(coming_events, key=lambda evt: (evt.start_date, evt.end_date))

    events_number = len(past_events) + len(coming_events)

    PREVIOUS_EVENT_URL_NAME = "ppage"
    NEXT_EVENT_URL_NAME = "npage"

    full_path = request.get_full_path()
    full_path = re.sub(r"\?|&" + PREVIOUS_EVENT_URL_NAME + r"=\d+", "", full_path)
    full_path = re.sub(r"\?|&" + NEXT_EVENT_URL_NAME + r"=\d+", "", full_path)

    paginatorComing = Paginator(coming_events, 8)
    paginatorPast = Paginator(past_events, 8)

    pageP = request.GET.get(PREVIOUS_EVENT_URL_NAME, 1)
    pageN = request.GET.get(NEXT_EVENT_URL_NAME, 1)

    try:
        coming_events = paginatorComing.page(pageN)
        past_events = paginatorPast.page(pageP)
    except PageNotAnInteger:
        pageP = 1
        pageN = 1
        coming_events = paginatorComing.page(1)
        past_events = paginatorPast.page(1)
    except EmptyPage:
        pageP = 1
        pageN = 1
        coming_events = paginatorComing.page(paginatorComing.num_pages)
        past_events = paginatorPast.page(paginatorPast.num_pages)

    return render(
        request,
        "live/my_events.html",
        {
            "full_path": full_path,
            "types": request.GET.getlist("type"),
            "events_number": events_number,
            "past_events": past_events,
            "past_events_url": PREVIOUS_EVENT_URL_NAME,
            "past_events_url_page": PREVIOUS_EVENT_URL_NAME + "=" + str(pageP),
            "coming_events": coming_events,
            "coming_events_url": NEXT_EVENT_URL_NAME,
            "coming_events_url_page": NEXT_EVENT_URL_NAME + "=" + str(pageN),
            "DEFAULT_EVENT_THUMBNAIL": DEFAULT_EVENT_THUMBNAIL,
            "display_broadcaster_name": True,
            "display_creation_button": can_manage_event(request.user),
            "page_title": _("My events"),
        },
    )


def get_event_edition_access(request, evt):
    # creation
    if evt is None:
        return can_manage_event(request.user)
    # edition
    return (
        request.user == evt.owner
        or request.user in evt.additional_owners.all()
        or request.user.is_superuser
    )


@csrf_protect
@ensure_csrf_cookie
@login_required(redirect_field_name="referrer")
def event_edit(request, slug=None):
    """View to edit the event identified by 'slug' (or plan a new one)."""
    if in_maintenance():
        return redirect(reverse("maintenance"))

    evt = get_object_or_404(Event, slug=slug) if slug else None

    if evt:
        page_title = _("Editing the event")
    else:
        page_title = _("Plan an event")

    if not get_event_edition_access(request, evt):
        return render(
            request,
            "live/event_edit.html",
            {
                "access_not_allowed": True,
                "page_title": page_title,
            },
        )

    form = EventForm(
        request.POST or None,
        instance=evt,
        user=request.user,
        is_current_event=evt.is_current() if slug else None,
        broadcaster_id=request.GET.get("broadcaster_id"),
        building_id=request.GET.get("building_id"),
    )

    if request.POST:
        form = EventForm(
            request.POST,
            instance=evt,
            user=request.user,
            is_current_event=evt.is_current() if slug else None,
        )
        if form.is_valid():
            evt = update_event(form)
            if EMAIL_ON_EVENT_SCHEDULING:
                send_email_confirmation(evt)
            messages.add_message(
                request, messages.INFO, _("The changes have been saved.")
            )
            return redirect(reverse("live:my_events"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request, "live/event_edit.html", {"form": form, "page_title": page_title}
    )


def update_event(form):
    """Update an event with received form fields."""
    if form.cleaned_data.get("end_date"):
        evt = form.save()
        return evt
    else:
        if form.cleaned_data.get("start_date"):
            d_debut = form.cleaned_data["start_date"].date()
        else:
            d_debut = datetime.now()

        evt = form.save(commit=False)
        d_fin = datetime.combine(d_debut, form.cleaned_data["end_time"])
        d_fin = timezone.make_aware(d_fin)
        evt.end_date = d_fin
        evt.save()
        return evt


@csrf_protect
@login_required(redirect_field_name="referrer")
def event_delete(request, slug=None):
    """Delete the event identified by 'slug'."""
    evt = get_object_or_404(Event, slug=slug)

    if request.user != evt.owner and not (
        request.user.is_superuser or request.user.has_perm("live.delete_event")
    ):
        messages.add_message(request, messages.ERROR, _("You cannot delete this event."))
        raise PermissionDenied

    form = EventDeleteForm()

    if request.method == "POST":
        form = EventDeleteForm(request.POST)
        if form.is_valid():
            evt.delete()
            messages.add_message(request, messages.INFO, _("The event has been deleted."))
            return redirect(reverse("live:my_events"))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "live/event_delete.html",
        {"event": evt, "form": form},
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def event_immediate_edit(request, broadcaster_id=None):
    if in_maintenance():
        return redirect(reverse("maintenance"))

    broadcaster = get_object_or_404(Broadcaster, id=broadcaster_id)

    page_title = _("Plan an immediate event")

    if not can_manage_event(request.user):
        return render(
            request,
            "live/event_edit.html",
            {
                "access_not_allowed": True,
                "page_title": page_title,
            },
        )

    my_event = Event()
    my_event.owner = request.user
    my_event.broadcaster = broadcaster
    my_event.is_auto_start = True

    form = EventImmediateForm(
        request.GET or None,
        user=request.user,
    )

    if request.POST:
        form = EventImmediateForm(
            request.POST,
            instance=my_event,
            user=request.user,
        )

        if form.is_valid():
            update_event(form)
            return redirect(reverse("live:event", kwargs={"slug": my_event.slug}))
        else:
            messages.add_message(
                request,
                messages.ERROR,
                _("One or more errors have been found in the form."),
            )

    return render(
        request,
        "live/event_immediate_edit.html",
        {"form": form, "broadcaster": broadcaster.id, "page_title": page_title},
    )


def broadcasters_from_building(request):
    building_name = request.GET.get("building")
    if not building_name:
        return HttpResponseBadRequest()
    build = Building.objects.filter(name=building_name).first()
    if not build:
        return HttpResponseNotFound()
    broadcasters = get_available_broadcasters_of_building(request.user, build.id)

    response_data = {}
    for broadcaster in broadcasters:
        response_data[broadcaster.id] = {
            "id": broadcaster.id,
            "name": broadcaster.name,
            "restricted": broadcaster.is_restricted,
        }
    return JsonResponse(response_data)


def broadcaster_restriction(request):
    if request.method == "GET":
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        if not broadcaster_id:
            return HttpResponseBadRequest()
        broadcaster = Broadcaster.objects.get(pk=broadcaster_id)
        return JsonResponse({"restricted": broadcaster.is_restricted})

    return HttpResponseNotAllowed(["GET"])


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_is_stream_available_to_record(request):
    """Check if the broadcaster is available to record and if is recording.

    Returns: a JsonResponse with available state and recording state of the broadcaster.
    """
    if request.method == "GET" and is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        broadcaster = Broadcaster.objects.get(pk=broadcaster_id)

        if not check_piloting_conf(broadcaster):
            return JsonResponse(
                {
                    "available": False,
                    "recording": False,
                    "message": "implementation error",
                }
            )

        if is_recording(broadcaster, True):
            return JsonResponse({"available": True, "recording": True})

        available = is_available_to_record(broadcaster)
        return JsonResponse({"available": available, "recording": False})

    return HttpResponseNotAllowed(["GET"])


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_startrecord(request):
    if request.method == "POST" and is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        return event_startrecord(event_id, broadcaster_id)

    return HttpResponseNotAllowed(["POST"])


def event_startrecord(event_id, broadcaster_id):
    """Calls the start method of the broadcaster's implementation.

    Returns: a JsonResponse with success state and the error (in case of failure).
    """
    broadcaster = Broadcaster.objects.get(pk=broadcaster_id)
    if not check_piloting_conf(broadcaster):
        return JsonResponse({"success": False, "error": "implementation error"})

    if is_recording(broadcaster):
        return JsonResponse(
            {"success": False, "error": "the broadcaster is already recording"}
        )

    if not start_record(broadcaster, event_id):
        return JsonResponse({"success": False, "error": ""})

    curr_event = Event.objects.get(pk=event_id)
    curr_event.is_recording_stopped = False

    return JsonResponse({"success": True})


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_splitrecord(request):
    if request.method == "POST" and is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)

        return event_splitrecord(event_id, broadcaster_id)

    return HttpResponseNotAllowed(["POST"])


def event_splitrecord(event_id, broadcaster_id):
    """Calls the split method of the broadcaster's implementation
    and converts the file to a Pod video (linked to the event).

     Returns: a JsonResponse with success state and the error (in case of failure).
    """
    broadcaster = Broadcaster.objects.get(pk=broadcaster_id)

    valid, res = check_event_record(broadcaster, with_file_check=True)
    if not valid:
        return res

    # file infos before split is done
    current_record_info = get_info_current_record(broadcaster)

    if not split_record(broadcaster):
        return JsonResponse({"success": False, "error": ""})

    return transform_to_video(
        broadcaster,
        event_id,
        current_record_info,
    )


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_stoprecord(request):
    if request.method == "POST" and is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        return event_stoprecord(event_id, broadcaster_id)

    return HttpResponseNotAllowed(["POST"])


def event_stoprecord(event_id, broadcaster_id):
    """Calls the stop method of the broadcaster's implementation
    and converts the file to a Pod video (linked to the event).

     Returns: a JsonResponse with success state and the error (in case of failure).
    """
    broadcaster = Broadcaster.objects.get(pk=broadcaster_id)

    valid, res = check_event_record(broadcaster, with_file_check=True)
    if not valid:
        return res
    current_record_info = get_info_current_record(broadcaster)

    if not stop_record(broadcaster):
        return JsonResponse({"success": False, "error": ""})

    # change is_recording_stopped property so the recording does not start again
    curr_event = Event.objects.get(pk=event_id)
    curr_event.is_recording_stopped = True
    curr_event.save()

    return transform_to_video(
        broadcaster,
        event_id,
        current_record_info,
    )


@login_required(redirect_field_name="referrer")
def ajax_event_info_record(request):
    if request.method == "POST" and is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        return event_info_record(event_id, broadcaster_id)

    return HttpResponseNotAllowed(["POST"])


def event_info_record(event_id, broadcaster_id):
    """Returns a JsonResponse with success state and :

    * the duration of the recording in seconds
    * or the error (in case of failure).
    """
    broadcaster = Broadcaster.objects.get(pk=broadcaster_id)
    valid, res = check_event_record(broadcaster)
    if not valid:
        return res
    current_record_info = get_info_current_record(broadcaster)

    if current_record_info.get("durationInSeconds") != "":
        return JsonResponse(
            {
                "success": True,
                "duration": int(current_record_info.get("durationInSeconds")),
            }
        )

    return JsonResponse({"success": False, "error": ""})


def check_event_record(broadcaster, with_file_check=False):
    """Checks whether the given broadcaster is recording an event."""
    if not check_piloting_conf(broadcaster):
        return False, JsonResponse({"success": False, "error": "implementation error"})

    if not is_recording(broadcaster, with_file_check):
        return False, JsonResponse(
            {"success": False, "error": "the broadcaster is not recording"}
        )

    return True, None


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_start_streaming(request):
    """Starts the stream."""
    return ajax_event_change_streaming(request, "start")


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_stop_streaming(request):
    """Stops the stream."""
    return ajax_event_change_streaming(request, "stop")


def ajax_event_change_streaming(request, action):
    """Starts or stops the stream."""
    if request.method != "POST" or not is_ajax(request):
        return HttpResponseNotAllowed(["POST"])

    if action not in ["start", "stop"]:
        return JsonResponse(
            {"success": False, "error": "can only start or stop"}, status=500
        )

    event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
    broadcaster = Broadcaster.objects.filter(pk=broadcaster_id).first()
    impl_class = get_piloting_implementation(broadcaster)

    if impl_class is None:
        return JsonResponse({"success": False, "error": "implementation error"})

    to_exe = impl_class.start_stream() if action == "start" else impl_class.stop_stream()

    if to_exe:
        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "error": f"{action} not done"})


@csrf_protect
@login_required(redirect_field_name="referrer")
def ajax_event_get_rtmp_config(request):
    """Checks if the broadcaster is configured for rtmp stream and return his config."""
    if request.method != "GET" or not is_ajax(request):
        return HttpResponseNotAllowed(["GET"])

    event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)

    broadcaster = Broadcaster.objects.get(pk=broadcaster_id)
    impl_class = get_piloting_implementation(broadcaster)

    if impl_class is None:
        return JsonResponse({"success": False, "error": "implementation error"})

    infos = impl_class.get_stream_rtmp_infos()
    if infos.get("error", ""):
        return JsonResponse({"success": False, "error": infos["error"]})

    return JsonResponse({"success": True, "data": infos})


@csrf_protect
def event_get_video_cards(request):
    """Returns the template with the videos link to the event."""
    if is_ajax(request):
        event_id, broadcaster_id = get_event_id_and_broadcaster_id(request)
        evt = Event.objects.get(pk=event_id)

        html = ""
        if evt.videos.count() > 0:
            request.resolver_match.namespace = ""
            html = render_to_string(
                "live/event_videos.html", {"event": evt}, request=request
            )
        return JsonResponse({"content": html})

    return HttpResponseBadRequest()


def create_video(event_id, current_file, segment_number):
    """Creates a video from the file_path given in the parameters."""
    live_event = Event.objects.get(pk=event_id)
    filename = os.path.basename(current_file)

    dest_file = os.path.join(
        settings.MEDIA_ROOT,
        VIDEOS_DIR,
        live_event.owner.owner.hashkey,
        filename,
    )

    dest_path = os.path.join(
        VIDEOS_DIR,
        live_event.owner.owner.hashkey,
        filename,
    )

    # dir creation if not exists
    dest_dir_name = os.path.dirname(dest_file)
    os.makedirs(dest_dir_name, exist_ok=True)

    try:
        check_dir_exists(dest_dir_name)

        # file creation if not exists
        full_file_name = os.path.join(DEFAULT_EVENT_PATH, filename)
        check_file_exists(full_file_name)

        # verif si la taille du fichier d'origine ne bouge plus
        check_size_not_changing(full_file_name)

        # moving the file
        os.rename(
            full_file_name,
            dest_file,
        )

        # verif si la taille du fichier copié ne bouge plus
        check_size_not_changing(dest_file)

    except Exception as exc:
        return JsonResponse(
            status=500,
            data={"success": False, "error": exc},
        )

    segment = "(" + segment_number + ")" if segment_number else ""

    adding_description = _("Record")
    if live_event.start_date.date() == live_event.end_date.date():
        adding_description += (
            " %s"
            % _("on %(start_date)s from %(start_time)s to %(end_time)s")
            % {
                "start_date": timezone.localtime(live_event.start_date).date(),
                "start_time": timezone.localtime(live_event.start_date).strftime("%H:%M"),
                "end_time": timezone.localtime(live_event.end_date).strftime("%H:%M"),
            }
        )
    else:
        adding_description += (
            " %s"
            % _("from %(start_date)s to %(end_date)s")
            % {
                "start_date": timezone.localtime(live_event.start_date),
                "end_date": timezone.localtime(live_event.end_date),
            }
        )

    video = Video.objects.create(
        video=dest_path,
        title=live_event.title + segment,
        owner=live_event.owner,
        description=live_event.description + "<br>" + adding_description,
        is_draft=live_event.is_draft,
        type=live_event.type,
    )
    if not live_event.is_draft:
        video.password = live_event.password
        video.is_restricted = live_event.is_restricted
        video.restrict_access_to_groups.set(live_event.restrict_access_to_groups.all())

    video.launch_encode = True
    video.save()

    live_event.videos.add(video)
    live_event.save()

    return JsonResponse({"success": True, "error": ""})


def check_dir_exists(dest_dir_name, max_attempt=6):
    """Checks a directory exists."""
    return check_exists(dest_dir_name, True, max_attempt)


def check_file_exists(full_file_name, max_attempt=6):
    """Checks a file exists."""
    return check_exists(full_file_name, False, max_attempt)


def check_piloting_conf(broadcaster: Broadcaster) -> bool:
    """Returns if the piloting configuration of the broadcaster is correct."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.check_piloting_conf() if impl_class else False


def start_record(broadcaster: Broadcaster, event_id) -> bool:
    """Starts the recording and return if successfully done."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.start_recording(event_id) if impl_class else False


def split_record(broadcaster: Broadcaster) -> bool:
    """Split the recording and return if successfully done."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.split_recording() if impl_class else False


def stop_record(broadcaster: Broadcaster) -> bool:
    """Stops the recording and return if successfully done."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.stop_recording() if impl_class else False


def use_split(broadcaster: Broadcaster) -> bool:
    """Returns if the implementation allows to split the current recording."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class is not None and impl_class.can_split()


def get_info_current_record(broadcaster: Broadcaster) -> dict:
    """Returns the infos of the current recording."""
    impl_class = get_piloting_implementation(broadcaster)
    if not impl_class:
        return {
            "currentFile": "",
            "segmentNumber": "",
            "outputPath": "",
            "durationInSeconds": "",
        }
    return impl_class.get_info_current_record()


def is_available_to_record(broadcaster: Broadcaster) -> bool:
    """Returns the broadcaster is ready to record."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.is_available_to_record() if impl_class else False


def is_recording(broadcaster: Broadcaster, with_file_check=False) -> bool:
    """Returns the broadcaster is actually recording."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class.is_recording(with_file_check) if impl_class else False


def transform_to_video(broadcaster, event_id, current_record_info):
    """
    Args:
        broadcaster (Broadcaster): the broadcaster
        event_id (int): event's id
        current_record_info(dict): infos

    Returns:
        JsonResponse: with success and error keys

    """
    impl_class = get_piloting_implementation(broadcaster)
    if not impl_class:
        return JsonResponse({"success": False, "error": "implementation error"})

    if impl_class.copy_file_needed():
        # Copie + transform faite dans un thread
        t = threading.Thread(
            target=copy_and_transform,
            args=[impl_class, event_id, current_record_info],
            daemon=True,
        )
        t.start()
        return JsonResponse({"success": True, "error": ""})

    return create_video(
        event_id,
        current_record_info.get("currentFile", None),
        current_record_info.get("segmentNumber", None),
    )


def copy_and_transform(impl_class, event_id, current_record_info):
    """
    Copies the file from remote to Pod and creates the video
    Args:
        impl_class (PilotingInterface): the piloting interface of the broadcaster
        event_id (int): event's id
        current_record_info(dict): infos

    Returns:
        bool: if successfully done

    """
    filename = current_record_info.get("currentFile", None)
    if impl_class.copy_file_to_pod_dir(filename):
        json_response = create_video(
            event_id,
            filename,
            current_record_info.get("segmentNumber", None),
        )
        return json_response.status_code == 200
    return False


def can_manage_stream(broadcaster: Broadcaster) -> bool:
    """Returns if the implementation allows to manage the stream."""
    impl_class = get_piloting_implementation(broadcaster)
    return impl_class is not None and impl_class.can_manage_stream()


def start_stream(broadcaster: Broadcaster) -> bool:
    """Starts the streaming and return if successfully done."""
    impl_class = get_piloting_implementation(broadcaster)
    if impl_class is None or not impl_class.can_manage_stream():
        return False

    rtmp_infos = impl_class.get_stream_rtmp_infos()
    if not rtmp_infos:
        return False

    if rtmp_infos["is_streaming"]:
        return True

    return impl_class.start_stream()


def stop_stream(broadcaster: Broadcaster) -> bool:
    """Stops the streaming and return if successfully done."""
    impl_class = get_piloting_implementation(broadcaster)
    if impl_class is None or not impl_class.can_manage_stream():
        return False

    rtmp_infos = impl_class.get_stream_rtmp_infos()
    if not rtmp_infos:
        return False

    if not rtmp_infos["is_streaming"]:
        return True

    return impl_class.stop_stream()
