"""
Esup-Pod - Management command: check_live_start_stop.

Start or stop broadcaster recordings based on live event schedules.
Port of V4's checkLiveStartStop command, rewritten to use the V5 service layer.
"""

from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from src.apps.live.models import Event
from src.apps.live.services.piloting import get_piloting_implementation

DEBUG = getattr(settings, "DEBUG", True)


class Command(BaseCommand):
    """Start or stop broadcaster recordings based on live events."""

    help = "Start or stop broadcaster recordings based on live events."

    debug_mode = DEBUG

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            help="Start and stop recording FOR REAL (disable dry-run mode).",
        )

    def handle(self, *args, **options):
        """Handle the check_live_start_stop command call."""
        if options["force"]:
            self.debug_mode = False

        self.stdout.write(
            f"== Beginning at {datetime.now().strftime('%H:%M:%S')} ",
            ending="",
        )
        self.stdout.write("IN DEBUG MODE ==" if self.debug_mode else "==")

        self.stop_finished()
        self.start_new()

        self.stdout.write(f"== End at {datetime.now().strftime('%H:%M:%S')} ==")
        self.stdout.write("")

    def stop_finished(self):
        """
        Stop all recordings of today's already-finished events that are not yet stopped.

        Includes non-auto-started events to be sure nothing is left recording.
        """
        self.stdout.write("- Stopping finished events (if started with Pod) -")

        now = timezone.localtime(timezone.now())
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        zero_now = now.replace(second=0, microsecond=0)

        events = (
            Event.objects.filter(
                end_date__gte=today,
                end_date__lte=zero_now,
                is_recording_stopped=False,
            )
            .order_by("end_date")
            .select_related("broadcaster")
        )

        for event in events:
            self.stdout.write(
                f"Event: '{event.slug}', on Broadcaster '{event.broadcaster.name}' ",
                ending="",
            )

            impl = get_piloting_implementation(event.broadcaster)

            if impl is None or not impl.is_recording(with_file_check=True):
                event.is_recording_stopped = True
                event.save(update_fields=["is_recording_stopped"])
                self.stdout.write("is already stopped")
                continue

            if self.debug_mode:
                self.stdout.write("should be stopped ... but not tried (debug mode)")
                continue

            self.stdout.write("should be stopped")
            success = impl.stop_recording()
            if success:
                Event.objects.filter(pk=event.pk).update(is_recording_stopped=True)
                self.stdout.write(" -> Record stopped")
                self._close_stream(event.broadcaster, impl)
            else:
                self.stderr.write(" -> Failed to stop recording")

    def start_new(self):
        """
        Start recordings for current events that have is_auto_start=True
        and have not been stopped yet.
        """
        self.stdout.write("- Starting new events -")

        now = timezone.localtime(timezone.now())
        events = Event.objects.filter(
            is_auto_start=True,
            is_recording_stopped=False,
            start_date__lte=now,
            end_date__gt=now,
        ).select_related("broadcaster")

        for event in events:
            self.stdout.write(
                f"Event: '{event.slug}', on Broadcaster '{event.broadcaster.name}'",
                ending="",
            )

            impl = get_piloting_implementation(event.broadcaster)

            if impl is None:
                self.stdout.write(" (no piloting implementation configured)")
                continue

            if impl.is_recording():
                self.stdout.write(" is already recording")
                continue

            if self.debug_mode:
                self.stdout.write(" should be started ... but not tried (debug mode)")
                continue

            self.stdout.write(" should be started")
            self._open_stream(event.broadcaster, impl)
            success = impl.start_recording(event.id)
            if success:
                Event.objects.filter(pk=event.pk).update(is_recording_stopped=False)
                self.stdout.write(" -> Record successfully started")
            else:
                self.stderr.write(" -> Failed to start record")

    def _open_stream(self, broadcaster, impl):
        """Try to open the RTMP stream for the broadcaster (SMP only)."""
        if impl.can_manage_stream():
            if impl.start_stream():
                self.stdout.write(" RTMP stream started")
            else:
                self.stderr.write(" RTMP stream not started")
        else:
            self.stdout.write(" Stream is not RTMP (will not try to start)")

    def _close_stream(self, broadcaster, impl):
        """Try to close the RTMP stream for the broadcaster (SMP only)."""
        if impl.can_manage_stream():
            if impl.stop_stream():
                self.stdout.write(" RTMP stream stopped")
            else:
                self.stderr.write(" RTMP stream not stopped")
        else:
            self.stdout.write(" Stream is not RTMP (will not try to stop)")
