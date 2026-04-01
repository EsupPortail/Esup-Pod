"""
Esup-Pod - Video application signals.
"""

import logging
import os

from django.contrib.sites.models import Site
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from src.apps.video.models import Video, Type
from src.apps.video.services.metadata import extract_video_duration

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=Video)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Esup-Pod - Deletes physical files from the disk when the Video object is deleted.
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
    Esup-Pod - Deletes the old file if a new version is uploaded for the same video.
    """
    if not instance.pk:
        return False

    try:
        old_file = Video.objects.get(pk=instance.pk).video_file
    except Video.DoesNotExist:
        return False

    new_file = instance.video_file
    if old_file and not old_file == new_file:
        if old_file.name and os.path.isfile(old_file.path):
            os.remove(old_file.path)


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    """
    Esup-Pod - At the time of creation (upload finished), calculate the duration.
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


@receiver(post_save, sender=Video)
def auto_assign_site_to_video(sender, instance, created, **kwargs):
    """
    Esup-Pod - Fallback signal: Ensures the video is linked to the current site
    if created via admin or other means.
    """
    if created:
        try:
            current_site = Site.objects.get_current()
            if not instance.sites.filter(pk=current_site.pk).exists():
                instance.sites.add(current_site)
        except Exception as e:
            logger.warning("Could not auto-assign site to video %s: %s", instance.pk, e)


@receiver(post_save, sender=Type)
def auto_assign_site_to_type(sender, instance, created, **kwargs):
    """
    Esup-Pod - Fallback signal: Ensures the type is linked to the current site
    if created via admin or other means.
    """
    if created:
        try:
            current_site = Site.objects.get_current()
            if not instance.sites.filter(pk=current_site.pk).exists():
                instance.sites.add(current_site)
        except Exception as e:
            logger.warning("Could not auto-assign site to type %s: %s", instance.pk, e)
