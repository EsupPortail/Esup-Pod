from django.core.management.base import BaseCommand
from pod.live.models import HeartBeat, Broadcaster
from django.utils import timezone


class Command(BaseCommand):
    help = 'Update viewcounter for lives'

    def handle(self, *args, **options):
        for hb in HeartBeat.objects.all():
            accepted_time = (timezone.now() - timezone.timedelta(minutes=1))
            if hb.last_heartbeat < accepted_time:
                hb.delete()
            else:
                hb.broadcaster.viewcount = hb.broadcaster.viewcount+1
        for broad in Broadcaster.objects.all():
            hbs = HeartBeat.objects.filter(broadcaster=broad)
            users = []
            for hb in hbs.all():
                if hb.user is not None and hb.user not in users:
                    users.append(hb.user)
            broad.viewers.set(users)
            broad.viewcount = hbs.count()
            broad.save()
