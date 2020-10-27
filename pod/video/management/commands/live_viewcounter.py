from django.core.management.base import BaseCommand
from pod.live.models import HeartBeat, Broadcaster
from django.utils import timezone
from django.conf import settings

VIEW_EXPIRATION_DELAY = getattr(
        settings, 'VIEW_EXPIRATION_DELAY', 60)


class Command(BaseCommand):
    help = 'Update viewcounter for lives'

    def handle(self, *args, **options):
        accepted_time = (
            timezone.now() - timezone.timedelta(
                seconds=VIEW_EXPIRATION_DELAY))
        for hb in HeartBeat.objects.all():
            if hb.last_heartbeat <= accepted_time:
                hb.delete()
        for broad in Broadcaster.objects.filter(enable_viewer_count=True):
            hbs = HeartBeat.objects.filter(broadcaster=broad)
            users = []
            for hb in hbs:
                if hb.user is not None and hb.user not in users:
                    users.append(hb.user)
            broad.viewers.set(users)
            broad.viewcount = hbs.count()
            broad.save()
