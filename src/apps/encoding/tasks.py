import logging

import requests.exceptions
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
    Retries automatically on connection errors (up to max_retries times).
    """
    logger.info("Triggering encoding task for video %s", video_id)
    video = get_object_or_404(Video, pk=video_id)

    try:
        from django.urls import reverse
        from django.conf import settings

        # We assume the webhook URL is /api/encoding/webhook/
        # We'll need to define this in urls.py later.
        # For now, we use a placeholder or better, we build it.
        # Note: In production, settings.SITE_URL or similar should be used.
        # The runner needs an absolute URL.
        webhook_path = reverse("encoding:webhook")
        # Base URL might be tricky in Celery. Let's try to pass it from the view if possible,
        # or use a setting. For now, let's assume we can construct it if we have the host.
        # Better: pass it as an argument to the task.

        # ACTUALLY: Let's use the source_url to guess the base URL if needed,
        # but the best way is to have a SITE_URL setting.
        site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
        notify_url = f"{site_url.rstrip('/')}{webhook_path}"

        client = get_runner_client()
        response = client.execute_task(
            video_id=str(video.slug),
            source_url=source_url,
            notify_url=notify_url,
            parameters={
                "video_id": str(video.id),
                "slug": video.slug,
                "title": video.title,
                "encoding_choices": ENCODING_CHOICES,
            },
        )
        logger.info(
            "Runner manager accepted task for video %s. Response: %s",
            video_id,
            response,
        )
        return response
    except requests.exceptions.RequestException as exc:
        # Network / connectivity errors from the runner client — retriable.
        logger.warning(
            "Connection error while triggering encoding for video %s "
            "(attempt %s/%s): %s",
            video_id,
            self.request.retries + 1,
            self.max_retries,
            exc,
        )
        raise self.retry(exc=exc)
    except Exception as exc:
        # Unexpected errors (bugs, DB issues, etc.) — not retriable.
        logger.error(
            "Unexpected error while triggering encoding for video %s: %s",
            video_id,
            exc,
            exc_info=True,
        )
        video.status = Video.Status.ERROR
        video.save(update_fields=["status"])
        logger.info(
            "Video %s status set to ERROR after unrecoverable encoding failure.",
            video_id,
        )
        raise
