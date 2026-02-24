import logging
from celery import shared_task
from django.shortcuts import get_object_or_404
from src.apps.video.models import Video
from src.apps.encoding.constants import ENCODING_CHOICES
from .services.runner_client import get_runner_client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_runner_encoding_task(self, video_id: int, source_url: str):
    """
    Triggers an encoding task on the runner manager for a given video.
    """
    logger.info(f"Triggering encoding task for video {video_id}")
    video = get_object_or_404(Video, pk=video_id)

    try:
        client = get_runner_client()
        response = client.execute_task(
            video_id=str(video.slug),
            source_url=source_url,
            parameters={
                "video_id": str(video.id),
                "slug": video.slug,
                "title": video.title,
                "encoding_choices": ENCODING_CHOICES,
                # any extra parameters can be added here
            },
        )
        logger.info(
            f"Runner manager accepted task for video {video_id}. Response: {response}"
        )
        return response
    except Exception as exc:
        logger.error(f"Failed to trigger encoding for video {video_id}: {exc}")
        video.status = Video.Status.ERROR
        video.save(update_fields=["status"])
        raise self.retry(exc=exc)
