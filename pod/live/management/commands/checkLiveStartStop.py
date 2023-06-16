"""start or stop broadcaster recording based on live events."""
import json
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q

from pod.live.models import Event
from pod.live.views import (
    can_manage_stream,
    event_stoprecord,
    event_startrecord,
    is_recording,
    start_stream,
    stop_stream,
)

DEFAULT_EVENT_PATH = getattr(settings, "DEFAULT_EVENT_PATH", "")
DEBUG = getattr(settings, "DEBUG", "")
TIME_ZONE = getattr(settings, "TIME_ZONE", "Europe/Paris")


class Command(BaseCommand):
    help = "start or stop broadcaster recording based on live events"

    debug_mode = DEBUG

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Start and stop recording FOR REAL",
        )

    def handle(self, *args, **options):
        """Handle the checkLiveStartStop command call."""
        if options["force"]:
            self.debug_mode = False

        self.stdout.write(
            f"== Beginning at {datetime.now().strftime('%H:%M:%S')} ", ending=""
        )
        self.stdout.write("IN DEBUG MODE ==" if self.debug_mode else "==")

        self.stop_finished()

        self.start_new()

        self.stdout.write(f"== End at {datetime.now().strftime('%H:%M:%S')} ==")
        self.stdout.write("")

    def stop_finished(self):
        """
        Stop all the recording of today's already finished events but yet not stopped.
        Including the non auto-started events (to be sure they are not forgotten).
        """
        self.stdout.write("- Stopping finished events (if started with Pod) -")

        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        zero_now = timezone.now().replace(second=0, microsecond=0)

        events = Event.objects.filter(
            Q(end_date__gte=today)
            & Q(end_date__lte=zero_now)
            & Q(is_recording_stopped=False)
        ).order_by("end_date")

        for event in events:
            self.stdout.write(
                f"Event : '{event.slug}', " f"on Broadcaster '{event.broadcaster_id}' ",
                ending="",
            )

            if not is_recording(event.broadcaster, True):
                event.is_recording_stopped = True
                event.save()
                self.stdout.write("is already stopped")
                continue

            if self.debug_mode:
                self.stdout.write("should be stopped ... but not tried (debug mode) ")
                continue

            self.stdout.write("should be stopped")

            response = event_stoprecord(event.id, event.broadcaster.id)
            if json.loads(response.content)["success"]:
                self.stdout.write(" -> Record stopped ")
            else:
                self.stderr.write(" -> Fail to stop recording")

            self.close_stream(event.broadcaster)

    def start_new(self):
        """
        Starts all recording of the current events
        that are auto-started configured and not stopped by manager.
        """
        self.stdout.write("- Starting new events -")

        events = Event.objects.filter(
            Q(is_auto_start=True)
            & Q(is_recording_stopped=False)
            & Q(start_date__lte=timezone.now())
            & Q(end_date__gt=timezone.now())
        )

        for event in events:
            self.stdout.write(
                f"Event : '{event.slug}', " f"on Broadcaster '{event.broadcaster_id}'",
                ending="",
            )

            if is_recording(event.broadcaster):
                self.stdout.write("is already recording")
                continue

            if self.debug_mode:
                self.stdout.write("should be started ... but not tried (debug mode) ")
                continue

            self.stdout.write("should be started")

            self.open_stream(event.broadcaster)

            response = event_startrecord(event.id, event.broadcaster.id)
            if json.loads(response.content)["success"]:
                self.stdout.write(" -> Record successfully started")
            else:
                self.stderr.write(" -> Fail to start record")

    def open_stream(self, broadcaster):
        """Try to open the broadcaster stream."""
        if can_manage_stream(broadcaster):
            if start_stream(broadcaster):
                self.stdout.write("RTMP stream started")
            else:
                self.stderr.write("RTMP stream not started")
        else:
            self.stdout.write("Stream is not RTMP (will not try to start)")

    def close_stream(self, broadcaster):
        """Try to close the broadcaster stream."""
        if can_manage_stream(broadcaster):
            started = stop_stream(broadcaster)
            if started:
                self.stdout.write("RTMP stream stopped")
            else:
                self.stderr.write("RTMP stream not stopped")
        else:
            self.stdout.write("Stream is not RTMP (will not try to stop)")
