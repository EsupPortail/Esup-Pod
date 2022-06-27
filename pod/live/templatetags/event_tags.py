from django import template
from datetime import date, datetime

from pod.live.models import Event

from django.db.models import Q

register = template.Library()


@register.simple_tag(takes_context=True)
def get_next_events(context, broadcaster_id=None, limit_nb=4):
    request = context["request"]
    queryset = Event.objects.filter(
        Q(start_date__gt=date.today())
        | (Q(start_date=date.today()) & Q(end_time__gte=datetime.now()))
    )
    # pour la supervision des evenements
    if broadcaster_id is not None:
        queryset = queryset.filter(broadcaster_id=broadcaster_id)
    if not request.user.is_authenticated():
        queryset = queryset.filter(is_draft=False)
        queryset = queryset.filter(is_restricted=False)
        queryset = queryset.filter(restrict_access_to_groups__isnull=False)

    return queryset.all().order_by("start_date", "start_time")[:limit_nb]
