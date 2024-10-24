from django.template.defaultfilters import register
from django.utils import timezone

from django.utils.translation import gettext_lazy as _
from pod.live.models import Event
from pod.live.views import can_manage_event
from pod.main.utils import generate_qrcode
from django.urls import reverse


@register.simple_tag(takes_context=True)
def get_next_events(context, broadcaster_id=None, limit_nb=4):
    request = context["request"]
    queryset = Event.objects.filter(start_date__gte=timezone.now())
    # pour la supervision des events
    if broadcaster_id is not None:
        queryset = queryset.filter(broadcaster_id=broadcaster_id)
    if not request.user.is_authenticated:
        queryset = queryset.filter(is_draft=False)
        # queryset = queryset.filter(is_restricted=False)
        # queryset = queryset.filter(restrict_access_to_groups__isnull=False)

    return queryset.all().order_by("start_date", "end_date")[:limit_nb]


@register.filter
def can_manage_event_filter(user):
    return can_manage_event(user)


@register.simple_tag(name="get_event_qrcode", takes_context=True)
def get_event_qrcode(context, event_id: int) -> str:
    """Get the event generated QR code.

    Args:
        event_id (int): Identifier of event object

    Returns:
        string: HTML-formed generated qrcode

    """
    request = context["request"]
    alt = _("QR code event’s link")
    url = reverse("live:event_immediate_edit", args={event_id})
    return generate_qrcode(url, alt, request)
