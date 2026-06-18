"""
Esup-Pod - Base abstract models for collections.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from src.apps.collection.conf import collection_settings


class BaseContainer(models.Model):
    """
    Abstract base class for all container types (Channel, Theme, Playlist).
    """

    ORDER_CHOICES = [
        ("-created_at", _("Newest first")),
        ("created_at", _("Oldest first")),
        ("title", _("Alphabetical (A-Z)")),
        ("-title", _("Alphabetical (Z-A)")),
    ]

    title = models.CharField(
        _("Title"),
        max_length=250,
        help_text=_("The title of the container."),
    )
    slug = models.SlugField(
        _("Slug"),
        unique=True,
        max_length=255,
        db_index=True,
        help_text=_("URL friendly identifier."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Full description of the content."),
    )
    old_v4_id = models.IntegerField(
        _("Old V4 ID"),
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Legacy ID from Pod V4 for migration/redirection."),
    )
    default_order = models.CharField(
        _("Default video ordering"),
        max_length=20,
        choices=ORDER_CHOICES,
        default=collection_settings.default_collection_order_field,
        help_text=_("The default order of videos inside this container."),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """BaseContainer model metadata."""

        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Handle slug generation."""
        from django.db import IntegrityError, transaction

        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            counter = 1
            while True:
                try:
                    with transaction.atomic():
                        super().save(*args, **kwargs)
                    break
                except IntegrityError:
                    self.slug = f"{base_slug}-{counter}"
                    counter += 1
        else:
            super().save(*args, **kwargs)
