from django.core.management.base import BaseCommand
from pod.live.models import HeartBeat, Event
from django.utils import timezone
from django.conf import settings

VIEW_EXPIRATION_DELAY = getattr(settings, "VIEW_EXPIRATION_DELAY", 60)


class Command(BaseCommand):
    help = "Update viewcounter for live events"

    def handle(self, *args, **options):

        # Suppression des Heartbeat trop anciens
        accepted_time = timezone.now() - timezone.timedelta(seconds=VIEW_EXPIRATION_DELAY)
        HeartBeat.objects.filter(last_heartbeat__lt=accepted_time).delete()

        # Suppression des viewers des events finis de la journée
        for finished_event in Event.objects.filter(
                start_date__date=timezone.now().date(),
                end_date__lt=timezone.now(),
                broadcaster__enable_viewer_count=True
        ).all():
            finished_event.viewers.set([])

        # Maj des viewers des events en cours
        for current_event in [evt for evt in Event.objects.all() if evt.is_current()]:
            hbs = HeartBeat.objects.filter(event=current_event)
            hbs = hbs.exclude(user=None)
            users = []
            for hb in hbs:
                if hb.user not in users:
                    users.append(hb.user)
            current_event.viewers.set(users)

            # faut-il garder le compteur sur le broadcaster pour le superviseur ?
            current_event.broadcaster.viewcount = hbs.count()

            current_event.save()
