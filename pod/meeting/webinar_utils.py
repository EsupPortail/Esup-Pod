"""Utils to manage webinars for Meeting module."""

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.handlers.wsgi import WSGIRequest
from django.core.mail import mail_admins
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import Meeting, LiveGateway, Livestream
from pod.live.models import Event
from pod.main.views import TEMPLATE_VISIBLE_SETTINGS
from pod.video.models import Type

__TITLE_SITE__ = (
    TEMPLATE_VISIBLE_SETTINGS["TITLE_SITE"]
    if (TEMPLATE_VISIBLE_SETTINGS.get("TITLE_SITE"))
    else "Pod"
)

DEFAULT_EVENT_TYPE_ID = getattr(settings, "DEFAULT_EVENT_TYPE_ID", 1)


def get_webinar_overlapping(meeting, webinar):
    """search if webinar overlapp a meeting."""
    webinar_overlapping = False
    meeting_end_date = meeting.start_at + meeting.expected_duration
    webinar_end_date = webinar.start_at + webinar.expected_duration
    # Search on the overlapping period
    if meeting.start_at >= webinar.start_at and meeting.start_at < webinar_end_date:
        webinar_overlapping = True
    elif meeting.start_at <= webinar.start_at and meeting_end_date > webinar.start_at:
        webinar_overlapping = True
    elif meeting.start_at >= webinar.start_at and meeting_end_date < webinar_end_date:
        webinar_overlapping = True
    elif meeting.start_at <= webinar.start_at and meeting_end_date > webinar_end_date:
        webinar_overlapping = True
    return webinar_overlapping


def search_for_available_livegateway(
    request: WSGIRequest, meeting: Meeting
) -> LiveGateway:
    """Search and returns a live gateway available during the period of the webinar.

    If more webinars are created than live gateways, an email is sent to warn administrators.
    In such a case, this function returns a None value.
    """
    site = get_current_site(request)
    # List of live gateways used
    live_gateways_id_used = []

    # Tip to allow same date format
    meeting = Meeting.objects.get(id=meeting.id)
    # All recent webinars - older webinars are not included (5h is max duration)
    # Not including the current webinar
    webinars_list = list(
        Meeting.objects.filter(
            is_webinar=True,
            start_at__gte=timezone.now() - timezone.timedelta(hours=5),
            site=site,
        ).exclude(id=meeting.id)
    )
    nb_webinars = 0
    names_webinars = ""
    # Search for live gateways at the same moment of this webinar
    for webinar in webinars_list:
        webinar_overlapping = get_webinar_overlapping(meeting, webinar)
        if webinar_overlapping:
            names_webinars += "%s, " % webinar.name
            nb_webinars += 1
            # Last livestream for the webinar
            livestream = (
                Livestream.objects.filter(meeting=webinar).order_by("-id").first()
            )
            if livestream:
                # Live gateway already used, add it to the list
                live_gateways_id_used.append(livestream.live_gateway.id)

    # Available live gateway at the same moment of this webinar
    live_gateway_available = (
        LiveGateway.objects.filter(site=site)
        .exclude(id__in=live_gateways_id_used)
        .first()
    )

    # Number total of live gateways
    nb_live_gateways = LiveGateway.objects.filter(site=site).count()
    # Remember that nb_webinars does not include the current webinar
    if nb_webinars + 1 > nb_live_gateways:
        # Send notification to administrators
        send_email_webinars(meeting, nb_webinars + 1, nb_live_gateways, names_webinars)

    # None possible
    return live_gateway_available


def send_email_webinars(
    meeting: Meeting, nb_webinars: int, nb_live_gateways: int, names_webinars: str
) -> None:
    """Send email notification to administrators when too many webinars."""
    subject = "[" + __TITLE_SITE__ + "] %s" % _("Too many webinars")
    message = _(
        "There are too many webinars (%(nb_webinars)s) for the number of "
        "live gateways allocated (%(nb_live_gateways)s). "
        "The next meeting has been created but not like a webinar: %(id)s %(name)s [%(start_at)s-%(end_at)s].\n"
        "Please fix the problem either by increasing the number of live gateways "
        "or by modifying/deleting one of the affected webinars "
        "(with the users’ agreement).\n"
        "Other webinars: %(names_webinars)s"
    ) % {
        "nb_webinars": nb_webinars,
        "nb_live_gateways": nb_live_gateways,
        "id": meeting.id,
        "name": meeting.name,
        "start_at": meeting.start_at,
        "end_at": meeting.start_at + meeting.expected_duration,
        "names_webinars": names_webinars,
    }

    html_message = _(
        "<p>There are too many webinars (<strong>%(nb_webinars)s</strong>) for the number of "
        "live gateways allocated (<strong>%(nb_live_gateways)s</strong>). "
        "The next webinar has been created but <strong>not like a webinar</strong>:"
        "<ul><li><strong>%(id)s %(name)s</strong> [%(start_at)s-%(end_at)s].</li></ul><p>"
        "Please fix the problem either by increasing the number of live gateways "
        "or by modifying/deleting one of the affected webinars "
        "(with the users’ agreement).<br>"
        "Other webinars: <strong>%(names_webinars)s</strong>"
    ) % {
        "nb_webinars": nb_webinars,
        "nb_live_gateways": nb_live_gateways,
        "id": meeting.id,
        "name": meeting.name,
        "start_at": meeting.start_at,
        "end_at": meeting.start_at + meeting.expected_duration,
        "names_webinars": names_webinars,
    }

    mail_admins(subject, message, fail_silently=False, html_message=html_message)


def update_livestream_event(livestream, meeting) -> None:
    """Update event livestream from meeeting attributes."""
    if livestream.event.title != meeting.name:
        livestream.event.title = meeting.name
    if livestream.event.start_date != meeting.start_at:
        livestream.event.start_date = meeting.start_at
    if livestream.event.end_date != meeting.start_at + meeting.expected_duration:
        livestream.event.end_date = meeting.start_at + meeting.expected_duration
    if livestream.event.is_restricted != meeting.is_restricted:
        livestream.event.is_restricted = meeting.is_restricted
    livestream.event.additional_owners.set(meeting.additional_owners.all())
    livestream.event.restrict_access_to_groups.set(
        meeting.restrict_access_to_groups.all()
    )

    # Update the livestream event
    livestream.event.save()


def manage_webinar(meeting: Meeting, created: bool, live_gateway: LiveGateway) -> None:
    """Manage the livestream and the event when a webinar is created or updated."""
    # When created a webinar
    if meeting.is_webinar and created:
        # No reccurence for a webinar
        meeting.reccurence = None
        meeting.save()
        # Create livestream and event
        create_livestream_event(meeting, live_gateway)

    # Search if a livestream exists for this meeting
    livestream = Livestream.objects.filter(meeting=meeting).first()

    # When updated a webinar
    if meeting.is_webinar and not created and livestream:
        # If update on meeting (for event-related fields) was achieved
        update_livestream_event(livestream, meeting)

    # When check is_webinar for an existent meeting
    if meeting.is_webinar and not created and not livestream:
        # Create livestream and event
        create_livestream_event(meeting, live_gateway)

    # When uncheck is_webinar for an existent meeting
    if not meeting.is_webinar and livestream:
        # Delete livestream and event if it's not a webinar (unchecked)
        livestream.event.delete()


def create_livestream_event(meeting: Meeting, live_gateway: LiveGateway) -> None:
    """Create a livestream and an event for a new webinar."""
    # Create live event
    event = Event.objects.create(
        title=meeting.name,
        owner=meeting.owner,
        broadcaster=live_gateway.broadcaster,
        type=Type.objects.get(id=DEFAULT_EVENT_TYPE_ID),
        start_date=meeting.start_at,
        end_date=meeting.start_at + meeting.expected_duration,
        is_draft=False,
        is_restricted=meeting.is_restricted,
    )
    event.restrict_access_to_groups.set(meeting.restrict_access_to_groups.all())

    # Create the livestream
    Livestream.objects.create(
        meeting=meeting,
        # Status: live not started
        status=0,
        event=event,
        live_gateway=live_gateway,
    )
