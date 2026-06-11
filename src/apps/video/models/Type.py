"""
Esup-Pod - Type model.
"""

from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Type(models.Model):
    """
    Model representing a video Type.
    """

    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=100, blank=True)
    sites = models.ManyToManyField(Site, related_name="video_types", blank=True)

    class Meta:
        """Type metadata."""

        verbose_name = _("Type")
        verbose_name_plural = _("Types")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug on save."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
