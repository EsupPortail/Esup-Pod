"""
Esup-Pod - Dressing application signals.
"""

import logging
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.conf import settings

from src.apps.dressing.models import Dressing

logger = logging.getLogger(__name__)


def trigger_encoding_for_video_ids(video_ids):
    """
    Helper function to trigger the Celery encoding task for a list of video IDs.
    """
    from src.apps.video.models import Video
    from src.apps.encoding.tasks import trigger_runner_encoding_task

    for video_id in video_ids:
        try:
            video = Video.objects.get(pk=video_id)
            if video.video_file:
                site_url = getattr(settings, "SITE_URL", "http://api:8000").rstrip("/")
                source_url = f"{site_url}{video.video_file.url}"
                logger.info(
                    "Dressing signal: triggering encoding for video %s (source_url=%s)",
                    video.id,
                    source_url,
                )
                trigger_runner_encoding_task.delay(video.pk, source_url)
            else:
                logger.warning(
                    "Dressing signal: video %s has no video_file, skipping encoding",
                    video.id,
                )
        except Video.DoesNotExist:
            logger.warning(
                "Dressing signal: video with ID %s not found, skipping encoding",
                video_id,
            )
        except Exception as e:
            logger.error(
                "Dressing signal: failed to trigger encoding for video %s: %s",
                video_id,
                e,
                exc_info=True,
            )


@receiver(m2m_changed, sender=Dressing.videos.through)
def dressing_videos_changed(sender, instance, action, pk_set, **kwargs):
    """
    Triggers re-encoding when a video is associated with or removed from a dressing.
    """
    if action in ("post_add", "post_remove"):
        if pk_set:
            logger.debug(
                "Dressing M2M signal (%s): triggering encoding for videos %s",
                action,
                pk_set,
            )
            trigger_encoding_for_video_ids(pk_set)
    elif action == "pre_clear":
        video_ids = list(instance.videos.values_list("id", flat=True))
        if video_ids:
            logger.debug(
                "Dressing M2M signal (pre_clear): triggering encoding for videos %s",
                video_ids,
            )
            trigger_encoding_for_video_ids(video_ids)


@receiver(post_save, sender=Dressing)
def dressing_post_save(sender, instance, created, **kwargs):
    """
    Triggers re-encoding for all associated videos when a dressing template is updated.
    """
    if not created:
        video_ids = list(instance.videos.values_list("id", flat=True))
        if video_ids:
            logger.debug(
                "Dressing post_save signal: dressing template '%s' updated. "
                "Triggering encoding for associated videos: %s",
                instance.title,
                video_ids,
            )
            trigger_encoding_for_video_ids(video_ids)
