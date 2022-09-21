import json
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from pod.live.models import Event
from pod.live.views import (
    is_recording,
    event_stoprecord,
    event_startrecord,
)

DEFAULT_EVENT_PATH = getattr(settings, "DEFAULT_EVENT_PATH", "")
DEBUG = getattr(settings, "DEBUG", "")
TIME_ZONE = getattr(settings, "TIME_ZONE", "Europe/Paris")


class Command(BaseCommand):
    help = "start or stop broadcaster recording based on live events "

    debug_mode = DEBUG

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Start and stop recording FOR REAL",
        )

    def handle(self, *args, **options):
        if options["force"]:
            self.debug_mode = False

        self.stdout.write(
            f"- Beginning at {datetime.now().strftime('%H:%M:%S')}", ending=""
        )
        self.stdout.write(" - IN DEBUG MODE -" if self.debug_mode else "")

        self.stop_finished()

        self.start_new()

        self.stdout.write("- End -")

    def stop_finished(self):
        self.stdout.write("-- Stopping finished events (if started with Pod) :")

        zero_now = timezone.now().replace(second=0, microsecond=0)
        # events ending now
        events = Event.objects.filter(end_date=zero_now)

        for event in events:
            if not is_recording(event.broadcaster, True):
                continue

            self.stdout.write(
                f"Broadcaster {event.broadcaster.name} should be stopped : ", ending=""
            )

            if self.debug_mode:
                self.stdout.write("... but not tried (debug mode) ")
                continue

            response = event_stoprecord(event.id, event.broadcaster.id)
            if json.loads(response.content)["success"]:
                self.stdout.write(" ...  stopped ")
            else:
                self.stderr.write(" ... fail to stop recording")

    def start_new(self):

        self.stdout.write("-- Starting new events :")

        events = Event.objects.filter(
            Q(is_auto_start=True)
            & Q(start_date__lte=timezone.now())
            & Q(end_date__gt=timezone.now())
        )

        for event in events:

            if is_recording(event.broadcaster):
                self.stdout.write(
                    f"Broadcaster {event.broadcaster.name} is already recording"
                )
                continue

            self.stdout.write(
                f"Broadcaster {event.broadcaster.name} should be started : ", ending=""
            )

            if self.debug_mode:
                self.stdout.write("... but not tried (debug mode) ")
                continue

            if event_startrecord(event.id, event.broadcaster.id):
                self.stdout.write(" ... successfully started")
            else:
                self.stderr.write(" ... fail to start")
