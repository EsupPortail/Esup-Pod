"""Update viewcounter for live events."""

from django.core.management.base import BaseCommand
from pod.live.models import HeartBeat, Event
from django.utils import timezone
from django.conf import settings

VIEW_EXPIRATION_DELAY = getattr(settings, "VIEW_EXPIRATION_DELAY", 60)


class Command(BaseCommand):
    help = "Update viewcounter for live events"

    def handle(self, *args, **options):
        """Handle the live_viewcounter command call."""
        # Suppression des Heartbeat trop anciens
        accepted_time = timezone.now() - timezone.timedelta(seconds=VIEW_EXPIRATION_DELAY)
        HeartBeat.objects.filter(last_heartbeat__lt=accepted_time).delete()

        # Suppression des viewers des events finis de la journée
        q = Event.objects.filter(
            start_date__date=timezone.now().date(),
            end_date__lt=timezone.now(),
            broadcaster__enable_viewer_count=True,
        )
        for finished_event in q.all():
            finished_event.viewers.set([])

        # Maj des viewers des events en cours
        events = Event.objects.all()

        for event in events:
            if event.is_current():
                hbs = HeartBeat.objects.filter(event=event)
                hbs = hbs.exclude(user=None)
                users = []
                for hb in hbs:
                    if hb.user not in users:
                        users.append(hb.user)
                event.viewers.set(users)
                event.save()
