from django.core.management.base import BaseCommand, CommandError
import os
import urllib.request
from django.conf import settings
from pod.video.models import Video
from pod.live.models import HeartBeat, Broadcaster
from django.utils import timezone



class Command(BaseCommand):
    help = 'Update viewcounter for lives'

    def handle(self, *args, **options):
        for hb in HeartBeat.objects.all():
            if hb.last_heartbeat < (timezone.now() - timezone.timedelta(minutes=1)):
                hb.delete()
            else:
                hb.broadcaster.viewcount = hb.broadcaster.viewcount+1
        for broad in Broadcaster.objects.all():
            broad.viewcount = HeartBeat.objects.filter(broadcaster=broad).count()
            broad.save()
        raise CommandError('WIP')
