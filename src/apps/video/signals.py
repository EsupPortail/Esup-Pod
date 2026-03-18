import logging
import os

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from src.apps.video.models import Video
from src.apps.video.services.metadata import extract_video_duration

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes physical files from the disk when the Video object is deleted.
    """
    if instance.video_file:
        if os.path.isfile(instance.video_file.path):
            os.remove(instance.video_file.path)
    if instance.thumbnail:
        if os.path.isfile(instance.thumbnail.path):
            os.remove(instance.thumbnail.path)
    if instance.overview:
        if os.path.isfile(instance.overview.path):
            os.remove(instance.overview.path)


@receiver(pre_save, sender=Video)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes the old file if a new version is uploaded for the same video.
    """
    if not instance.pk:
        return False

    try:
        old_file = Video.objects.get(pk=instance.pk).video_file
    except Video.DoesNotExist:
        return False

    new_file = instance.video_file
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    At the time of creation (upload finished), calculate the duration
    and set the video to PUBLISHED (since we don't do complex encoding for now).
    """
    logger.debug(
        "video_post_save triggered. created=%s, file=%s",
        created,
        instance.video_file,
    )
    if created and instance.video_file:
        if instance.duration == 0:
            file_path = instance.video_file.path
            logger.debug(
                "Processing file at %s. exists=%s",
                file_path,
                os.path.exists(file_path),
            )
            if os.path.exists(file_path):
                duration = extract_video_duration(file_path)
                logger.debug(
                    "Extracted duration=%s. Updating status to PUBLISHED...", duration
                )
                Video.objects.filter(pk=instance.pk).update(duration=duration)
                logger.info(
                    "Video pk=%s published with duration=%ss.", instance.pk, duration
                )
