"""
Esup-Pod - Celery tasks for the encoding app.

This module contains tasks for triggering and retrying encoding jobs.
"""

import logging
import json
import requests.exceptions

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from .conf import encoding_settings
from config.env import env

from src.apps.video.models import Video
from .services.runner_client import get_runner_client

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def trigger_runner_encoding_task(self, video_id: int, source_url: str):
    """
    Triggers an encoding task on the runner manager for a given video.
    Retries automatically on connection errors (up to max_retries times).
    """
    logger.info("Triggering encoding task for video %s", video_id)

    try:
        video = Video.objects.get(pk=video_id)
    except ObjectDoesNotExist:
        logger.error("Video %s not found. Aborting encoding task.", video_id)
        return None

    # Signal immediately that encoding has started.
    Video.objects.filter(pk=video_id).update(
        encoding_status=Video.EncodingStatus.PROCESSING
    )

    try:
        webhook_path = reverse("encoding:webhook")
        site_url = encoding_settings.site_url
        webhook_secret = env("ENCODING_WEBHOOK_SECRET", default="")
        notify_url = f"{site_url.rstrip('/')}{webhook_path}?secret={webhook_secret}&video_id={video_id}"

        rendition_config = {
            "360": {"resolution": "640x360", "encode_mp4": True},
            "720": {"resolution": "1280x720", "encode_mp4": True},
            "1080": {"resolution": "1920x1080", "encode_mp4": False},
        }

        parameters = {"rendition": json.dumps(rendition_config)}

        dressing = video.videos_dressing.first()
        if dressing:
            dressing_params = dressing.to_runner_parameters()
            for key in ["watermark", "opening_credits_video", "ending_credits_video"]:
                if key in dressing_params and dressing_params[key].startswith("/"):
                    dressing_params[key] = f"{site_url.rstrip('/')}{dressing_params[key]}"
            parameters["dressing"] = json.dumps(dressing_params)

        logger.error(f"DEBUG: sending notify_url={notify_url}")

        client = get_runner_client()
        response = client.execute_task(
            video_id=str(video.slug),
            source_url=source_url,
            notify_url=notify_url,
            parameters=parameters,
        )

        logger.info(
            "Runner manager accepted task for video %s. Response: %s",
            video_id,
            response,
        )
        return response

    except requests.exceptions.RequestException as exc:
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
        logger.error(
            "Unexpected error while triggering encoding for video %s: %s",
            video_id,
            exc,
            exc_info=True,
        )
        Video.objects.filter(pk=video_id).update(
            encoding_status=Video.EncodingStatus.ERROR
        )
        raise
