"""
Esup-Pod - Channel model.
"""

import logging
from django.db import models
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from src.apps.collection.models.base import BaseContainer
from src.apps.encoding.services.storage import get_storage_path_collection_image
from src.apps.utils.files import safe_remove_file

logger = logging.getLogger(__name__)


class Channel(BaseContainer):
    """
    Model representing a channel.
    A channel is the identity of a creator or a service.
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_channels",
        verbose_name=_("Owner"),
    )
    is_public = models.BooleanField(
        _("Is Public"),
        default=True,
        help_text=_("If unchecked, the channel is private."),
    )
    logo = models.ImageField(
        _("Logo"),
        upload_to=get_storage_path_collection_image,
        null=True,
        blank=True,
        help_text=_("Channel logo or square icon."),
    )
    banner = models.ImageField(
        _("Banner"),
        upload_to=get_storage_path_collection_image,
        null=True,
        blank=True,
        help_text=_("Large banner for the channel header."),
    )
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="collaborated_channels",
        verbose_name=_("Collaborators"),
        help_text=_("Users with permissions to manage this channel."),
    )

    class Meta(BaseContainer.Meta):
        """Channel model metadata."""

        verbose_name = _("Channel")
        verbose_name_plural = _("Channels")


@receiver(post_delete, sender=Channel)
def auto_delete_channel_files_on_delete(sender, instance, **kwargs):
    """
    Deletes physical logo and banner files from disk when Channel object is deleted.
    """
    safe_remove_file(instance.logo)
    safe_remove_file(instance.banner)
