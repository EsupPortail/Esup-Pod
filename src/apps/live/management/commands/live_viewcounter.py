"""
Esup-Pod - Management command: live_viewcounter.

Update the viewer count for live events by syncing HeartBeat records
into Event.viewers (authenticated users only) and clearing stale heartbeats.

Port of V4's live_viewcounter command.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from src.apps.live.models import Event, HeartBeat
from src.apps.live.conf import live_settings


class Command(BaseCommand):
    """Update viewer count for live events."""

    help = "Update viewcounter for live events and clean up stale heartbeats."

    def handle(self, *args, **options):
        """Handle the live_viewcounter command call."""
        now = timezone.now()

        # 1. Remove expired heartbeats (older than 2x heartbeat_delay, consistent with cleanup_stale)
        expiry_threshold = now - timezone.timedelta(
            seconds=live_settings.heartbeat_delay * 2
        )
        deleted_count, _ = HeartBeat.objects.filter(
            last_heartbeat__lt=expiry_threshold
        ).delete()
        self.stdout.write(f"Deleted {deleted_count} stale heartbeat(s).")

        # 2. Clear viewers for events that have ended today
        finished_events = Event.objects.filter(
            start_date__date=now.date(),
            end_date__lt=now,
            broadcaster__enable_viewer_count=True,
        )
        cleared = 0
        for event in finished_events:
            event.viewers.clear()
            cleared += 1
        self.stdout.write(f"Cleared viewers for {cleared} finished event(s).")

        # 3. Sync Event.viewers with authenticated heartbeat users for active events
        updated = 0
        for event in Event.objects.all():
            if event.is_current():
                authenticated_heartbeats = (
                    HeartBeat.objects.filter(event=event)
                    .exclude(user=None)
                    .select_related("user")
                )

                # Deduplicate users
                user_ids = list(
                    dict.fromkeys(hb.user_id for hb in authenticated_heartbeats)
                )
                event.viewers.set(user_ids)
                updated += 1

        self.stdout.write(f"Updated viewers for {updated} active event(s).")
        self.stdout.write(self.style.SUCCESS("live_viewcounter completed successfully."))
