"""
Esup-Pod - Video Celery tasks.
"""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def task_bulk_update_videos(video_ids: list, fields: dict, user_id: int) -> None:
    """
    Celery task for bulk updating videos asynchronously.
    Applied when more than BULK_ASYNC_THRESHOLD videos are selected.
    """
    from django.db import transaction
    from src.apps.video.models import Video

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("Bulk update: user %s not found.", user_id)
        return

    videos = Video.objects.filter(id__in=video_ids)

    try:
        with transaction.atomic():
            for video in videos:
                for attr, value in fields.items():
                    setattr(video, attr, value)
                video.save()
        logger.info(
            "Bulk update completed: %s videos updated by user %s.",
            videos.count(),
            user.username,
        )
    except Exception as e:
        logger.exception("Bulk update failed for user %s: %s", user_id, e)


@shared_task
def task_bulk_delete_videos(video_ids: list, user_id: int) -> None:
    """
    Celery task for bulk deleting videos asynchronously.
    Applied when more than BULK_ASYNC_THRESHOLD videos are selected.
    """
    from django.db import transaction
    from src.apps.video.models import Video

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.error("Bulk delete: user %s not found.", user_id)
        return

    videos = Video.objects.filter(id__in=video_ids)

    try:
        with transaction.atomic():
            deleted_count, _ = videos.delete()
        logger.info(
            "Bulk delete completed: %s videos deleted by user %s.",
            deleted_count,
            user.username,
        )
    except Exception as e:
        logger.exception("Bulk delete failed for user %s: %s", user_id, e)
