"""
Esup-Pod - Theme model for taxonomy.
"""

from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from src.apps.collection.models.base import BaseContainer
from src.apps.collection.models.Channel import Channel
from src.apps.video.models.Video import Video
from src.apps.encoding.services.storage import get_storage_path_collection_image
from src.apps.utils.files import safe_remove_file


class Theme(BaseContainer):
    """
    Model representing a thematic category.
    Themes are part of a global taxonomy managed by administrators,
    or can be specific to a channel if OWNER_CAN_MANAGE_THEMES is enabled.
    """

    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="themes",
        verbose_name=_("Channel"),
        help_text=_("The channel this theme belongs to (if not global)."),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name=_("Parent Theme"),
        help_text=_("The parent theme to create a hierarchy."),
    )
    videos = models.ManyToManyField(
        Video,
        through="ThemeItem",
        related_name="themes",
        verbose_name=_("Videos"),
        blank=True,
    )
    banner = models.ImageField(
        _("Banner"),
        upload_to=get_storage_path_collection_image,
        null=True,
        blank=True,
        help_text=_("Large banner for the theme page."),
    )

    class Meta(BaseContainer.Meta):
        """Theme model metadata."""

        verbose_name = _("Theme")
        verbose_name_plural = _("Themes")

    def clean(self):
        """Validate the theme to prevent circular references in the parent hierarchy."""
        from django.core.exceptions import ValidationError

        if self.parent:
            if self.parent == self:
                raise ValidationError({"parent": _("A theme cannot be its own parent.")})

            current_parent = self.parent
            while current_parent is not None:
                if current_parent.pk == self.pk and self.pk is not None:
                    raise ValidationError(
                        {"parent": _("Circular reference detected in theme hierarchy.")}
                    )
                current_parent = current_parent.parent

            if self.parent.channel != self.channel:
                raise ValidationError(
                    {
                        "parent": _(
                            "A sub-theme must belong to the same channel as its parent."
                        )
                    }
                )

    def save(self, *args, **kwargs):
        """Run validation before saving to enforce hierarchy integrity."""
        self.clean()
        super().save(*args, **kwargs)


class ThemeItem(models.Model):
    """
    Join table between Theme and Video.
    """

    theme = models.ForeignKey(Theme, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """ThemeItem model metadata."""

        verbose_name = _("Theme Item")
        verbose_name_plural = _("Theme Items")
        unique_together = ("theme", "video")


@receiver(post_delete, sender=Theme)
def auto_delete_theme_banner_on_delete(sender, instance, **kwargs):
    """
    Deletes physical banner file from disk when Theme object is deleted.
    """
    safe_remove_file(instance.banner)
