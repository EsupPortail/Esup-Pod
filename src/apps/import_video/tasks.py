"""
Esup-Pod - Import Video Celery tasks.
"""

import logging
import os

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from src.apps.import_video.models import ExternalRecording

logger = logging.getLogger(__name__)
User = get_user_model()


def _get_dest_path(recording: ExternalRecording, filename: str) -> str:
    """Builds the destination path for a downloaded video file."""
    from django.conf import settings

    return os.path.join(
        settings.MEDIA_ROOT,
        "videos",
        f"import_{recording.id}",
        filename,
    )


def _create_video_from_recording(
    recording: ExternalRecording, file_path: str, title: str, user
) -> None:
    """
    Creates a Video object from the downloaded file and links it to the recording.
    Triggers encoding pipeline.
    """
    from django.contrib.sites.models import Site
    from django.core.files import File

    from src.apps.video.models import Video
    from src.apps.video.conf import video_settings
    from src.apps.encoding.tasks import trigger_runner_encoding_task

    with open(file_path, "rb") as f:
        video = Video.objects.create(
            title=title,
            owner=user,
            status=Video.Status.DRAFT,
        )
        video.video_file.save(os.path.basename(file_path), File(f), save=True)

    current_site = Site.objects.get_current()
    video.sites.add(current_site)

    recording.video = video
    recording.import_status = ExternalRecording.ImportStatus.DONE
    recording.imported_at = timezone.now()
    recording.save(update_fields=["video", "import_status", "imported_at"])

    site_url = video_settings.site_url.rstrip("/")
    source_url = f"{site_url}{video.video_file.url}"
    trigger_runner_encoding_task.delay(video.pk, source_url)

    logger.info("Video created and encoding triggered for recording %s", recording.id)


def _dispatch_import(recording: ExternalRecording) -> tuple:
    """
    Dispatches the import to the appropriate service based on source_type.
    Returns a tuple (file_path, title).
    """
    source_type = recording.source_type
    source_url = recording.source_url

    if source_type == ExternalRecording.SourceType.YOUTUBE:
        from src.apps.import_video.services.youtube import (
            download_youtube_video,
            get_youtube_metadata,
        )

        metadata = get_youtube_metadata(source_url)
        dest_dir = _get_dest_path(recording, "")
        file_path = download_youtube_video(source_url, dest_dir)
        return file_path, metadata.get("title", recording.name)

    if source_type == ExternalRecording.SourceType.PEERTUBE:
        from src.apps.import_video.services.peertube import (
            download_peertube_video,
            get_peertube_metadata,
        )

        metadata = get_peertube_metadata(source_url)
        dest_path = _get_dest_path(recording, f"{recording.id}_peertube.mp4")
        file_path = download_peertube_video(source_url, dest_path)
        return file_path, metadata.get("title", recording.name)

    if source_type == ExternalRecording.SourceType.BBB:
        from src.apps.import_video.services.bbb import (
            download_bbb_video,
            get_bbb_standard_metadata,
        )

        metadata = get_bbb_standard_metadata(source_url)
        dest_path = _get_dest_path(recording, f"{recording.id}_bbb.mp4")
        file_path = download_bbb_video(source_url, dest_path)
        return file_path, metadata.get("title", recording.name)

    if source_type == ExternalRecording.SourceType.VIDEO_FILE:
        from src.apps.import_video.services.downloader import download_file

        dest_path = _get_dest_path(recording, f"{recording.id}_video.mp4")
        file_path = download_file(source_url, dest_path)
        return file_path, recording.name

    if source_type == ExternalRecording.SourceType.MEDIACAD:
        from src.apps.import_video.services.mediacad import (
            download_mediacad_video,
            get_mediacad_metadata,
        )

        metadata = get_mediacad_metadata(source_url)
        dest_path = _get_dest_path(recording, f"{recording.id}_mediacad.mp4")
        file_path = download_mediacad_video(source_url, dest_path)
        return file_path, metadata.get("title", recording.name)

    raise ValueError(f"Unsupported source type: {source_type}")


@shared_task
def task_import_external_recording(recording_id: int, user_id: int) -> None:
    """
    Celery task that imports an external recording into Pod.
    Dispatches to the appropriate service based on source_type.
    Updates import_status throughout the process.
    """
    try:
        recording = ExternalRecording.objects.get(pk=recording_id)
        user = User.objects.get(pk=user_id)
    except ExternalRecording.DoesNotExist:
        logger.error("ExternalRecording %s not found.", recording_id)
        return
    except User.DoesNotExist:
        logger.error("User %s not found.", user_id)
        return

    recording.import_status = ExternalRecording.ImportStatus.PROCESSING
    recording.save(update_fields=["import_status"])

    try:
        file_path, title = _dispatch_import(recording)
        _create_video_from_recording(recording, file_path, title, user)

    except NotImplementedError as e:
        logger.warning("Import not implemented for recording %s: %s", recording_id, e)
        recording.import_status = ExternalRecording.ImportStatus.ERROR
        recording.error_message = str(e)
        recording.save(update_fields=["import_status", "error_message"])

    except ValueError as e:
        logger.error("Import failed for recording %s: %s", recording_id, e)
        recording.import_status = ExternalRecording.ImportStatus.ERROR
        recording.error_message = str(e)
        recording.save(update_fields=["import_status", "error_message"])

    except Exception as e:
        logger.exception("Unexpected error importing recording %s", recording_id)
        recording.import_status = ExternalRecording.ImportStatus.ERROR
        recording.error_message = _("Unexpected error: %(error)s") % {"error": e}
        recording.save(update_fields=["import_status", "error_message"])
