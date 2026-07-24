"""
Esup-Pod - Live background tasks.

Asynchronous tasks for:
- Automatic recording scheduling (start/stop based on event time windows)
- Video ingestion after a live event ends (file copy + Video model creation)
- Heartbeat cleanup
- Live transcription management (start/stop via Celery)

Ported and modernised from V4 pod/live/views.py and pod/main/tasks.py.
"""

import logging
import os
import shutil

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.apps.live.models import Event, HeartBeat
from src.apps.live.services.piloting import (
    get_piloting_implementation,
    CREATE_VIDEO_FROM_FTP,
    CREATE_VIDEO_FROM_FS,
    CREATE_VIDEO_OPENCAST,
)
from src.apps.live.conf import live_settings
from src.apps.live.utils import (
    check_dir_exists,
    check_file_exists,
    check_size_not_changing,
)
from src.apps.video.models import Video

logger = logging.getLogger(__name__)

VIDEOS_DIR = getattr(settings, "VIDEOS_DIR", "videos")


# ---------------------------------------------------------------------------
# Recording automation
# ---------------------------------------------------------------------------


@shared_task
def manage_auto_recordings_task():
    """
    Periodic task to automatically start and stop recordings
    for events with is_auto_start=True.
    Scheduled via Celery Beat (e.g., every minute).
    """
    now = timezone.localtime(timezone.now())

    # 1. Start imminent recordings
    starting_events = Event.objects.filter(
        is_auto_start=True,
        is_recording_stopped=False,
        start_date__lte=now,
        end_date__gt=now,
    )
    for event in starting_events:
        impl = get_piloting_implementation(event.broadcaster)
        if impl:
            if not impl.is_recording():
                logger.info("Auto-starting recording for Event %s", event.id)
                success = impl.start_recording(event.id)
                if not success:
                    logger.error("Failed to auto-start recording for Event %s", event.id)

    # 2. Stop finished recordings
    ending_events = Event.objects.filter(
        is_auto_start=True,
        is_recording_stopped=False,
        end_date__lte=now,
    )
    for event in ending_events:
        impl = get_piloting_implementation(event.broadcaster)
        if impl:
            logger.info("Auto-stopping recording for Event %s", event.id)
            if impl.is_recording():
                impl.stop_recording()

        # Mark as stopped so we don't try again
        Event.objects.filter(pk=event.pk).update(is_recording_stopped=True)

        # Trigger video retrieval workflow
        retrieve_recorded_video_task.delay(event.id)


# ---------------------------------------------------------------------------
# Video ingestion
# ---------------------------------------------------------------------------


@shared_task
def retrieve_recorded_video_task(event_id: int):
    """
    Orchestrate the post-event video creation.

    Fetches recording info from the piloting implementation,
    then delegates to the appropriate creation strategy
    (FTP copy, filesystem move, or Opencast passthrough).
    """
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        logger.error("Event %s not found for video retrieval.", event_id)
        return

    impl = get_piloting_implementation(event.broadcaster)
    if not impl:
        logger.error("No piloting implementation for broadcaster of Event %s", event_id)
        return

    current_record_info = impl.get_info_current_record()
    vcm = impl.video_creation_method()

    if vcm == CREATE_VIDEO_OPENCAST:
        logger.info("Event %s uses Opencast — no manual video creation needed.", event_id)
        return

    elif vcm == CREATE_VIDEO_FROM_FTP:
        # Copy file from remote, then create the Video entry
        filename = current_record_info.get("currentFile")
        if impl.copy_file_to_pod_dir(filename):
            _create_video_from_file(
                event, filename, current_record_info.get("segmentNumber")
            )
        else:
            logger.error(
                "Failed to copy file %s from broadcaster %s",
                filename,
                event.broadcaster.name,
            )

    elif vcm == CREATE_VIDEO_FROM_FS:
        _create_video_from_file(
            event,
            current_record_info.get("currentFile"),
            current_record_info.get("segmentNumber"),
        )


def _build_video_description(event) -> str:
    """Build a human-readable recording description based on event dates (ported from V4)."""
    desc = str(_("Record"))
    start = timezone.localtime(event.start_date)
    end = timezone.localtime(event.end_date)

    if event.start_date.date() == event.end_date.date():
        desc += " %s" % (
            _("on %(start_date)s from %(start_time)s to %(end_time)s")
            % {
                "start_date": start.date(),
                "start_time": start.strftime("%H:%M"),
                "end_time": end.strftime("%H:%M"),
            }
        )
    else:
        desc += " %s" % (
            _("from %(start_date)s to %(end_date)s")
            % {
                "start_date": start,
                "end_date": end,
            }
        )
    return desc


def _create_video_from_file(event, current_file: str, segment_number: str) -> bool:
    """
    Move the recorded file to the owner's video folder and create the Video entry.

    This is a direct port of the V4 create_video() logic, adapted to use
    the V5 Video model field names.

    Returns:
        True on success, False on failure.
    """
    if not current_file:
        logger.warning("No current file provided for Event %s", event.id)
        return False

    filename = os.path.basename(current_file)

    # Determine destination paths
    try:
        owner_hashkey = event.owner.owner.hashkey
    except AttributeError:
        owner_hashkey = str(event.owner.pk)

    dest_file = os.path.join(
        settings.MEDIA_ROOT,
        VIDEOS_DIR,
        owner_hashkey,
        filename,
    )
    dest_path = os.path.join(VIDEOS_DIR, owner_hashkey, filename)
    dest_dir_name = os.path.dirname(dest_file)
    os.makedirs(dest_dir_name, exist_ok=True)

    try:
        check_dir_exists(dest_dir_name)
        full_file_name = os.path.join(live_settings.default_event_path, filename)
        check_file_exists(full_file_name)
        check_size_not_changing(full_file_name)

        # Copy then delete — avoids cross-filesystem rename issues (containerised envs)
        shutil.copyfile(full_file_name, dest_file)
        check_size_not_changing(dest_file)
        os.remove(full_file_name)

    except Exception as exc:
        logger.error("Failed to move recorded file for Event %s: %s", event.id, exc)
        return False

    # Build segment suffix
    segment = ("(" + segment_number + ")") if segment_number else ""
    adding_description = _build_video_description(event)

    video = Video.objects.create(
        video_file=dest_path,
        title=event.title + segment,
        owner=event.owner,
        description=event.description + "<br>" + adding_description,
        is_draft=event.is_draft,
        type=event.type,
    )

    # Inherit access restrictions from the event (as in V4)
    if not event.is_draft:
        video.password = event.password
        video.is_restricted = event.is_restricted
        video.restrict_access_to_groups.set(event.restrict_access_to_groups.all())

    video.save()
    event.videos.add(video)
    event.save()

    logger.info("Successfully created Video %s for Event %s", video.id, event.id)
    return True


# ---------------------------------------------------------------------------
# Heartbeat cleanup
# ---------------------------------------------------------------------------


@shared_task
def cleanup_heartbeats_task():
    """
    Periodically clear stale heartbeats across all active events.
    Also clears Event.viewers for events that have ended today.
    Scheduled via Celery Beat (e.g., every 5 minutes).
    """
    now = timezone.localtime(timezone.now())
    active_events = Event.objects.filter(start_date__lte=now, end_date__gt=now)
    for event in active_events:
        HeartBeat.cleanup_stale(event, live_settings.heartbeat_delay)

    # Mirror V4 live_viewcounter: clear viewers list for finished events of the day
    finished_events = Event.objects.filter(
        start_date__date=now.date(),
        end_date__lte=now,
        broadcaster__enable_viewer_count=True,
    )
    for event in finished_events:
        event.viewers.clear()


# ---------------------------------------------------------------------------
# Live transcription tasks (ported from V4 pod/main/tasks.py)
# ---------------------------------------------------------------------------


@shared_task(bind=True)
def start_live_transcription_task(
    self, url: str, slug: str, model_path: str, filepath: str
) -> None:
    """Start live transcription with Celery, tracking the task ID."""
    logger.info("CELERY START LIVE TRANSCRIPTION %s", slug)
    from src.apps.live.services.transcription import transcribe
    from src.apps.live.models import Broadcaster, LiveTranscriptRunningTask

    try:
        broadcaster = Broadcaster.objects.get(slug=slug)
        LiveTranscriptRunningTask.objects.create(
            broadcaster=broadcaster, task_id=self.request.id
        )
        transcribe(url, slug, model_path, filepath)
    except Broadcaster.DoesNotExist:
        logger.error("Broadcaster %s not found for transcription.", slug)


@shared_task(bind=True)
def end_live_transcription_task(self, slug: str) -> None:
    """Revoke and clean up the live transcription task for a broadcaster."""
    logger.info("CELERY END LIVE TRANSCRIPTION %s", slug)
    from src.apps.live.models import Broadcaster, LiveTranscriptRunningTask

    try:
        broadcaster = Broadcaster.objects.get(slug=slug)
        running_task = LiveTranscriptRunningTask.objects.filter(
            broadcaster=broadcaster
        ).first()
        if running_task:
            self.app.control.revoke(running_task.task_id, terminate=True)
            running_task.delete()
    except Broadcaster.DoesNotExist:
        logger.error("Broadcaster %s not found for ending transcription.", slug)
