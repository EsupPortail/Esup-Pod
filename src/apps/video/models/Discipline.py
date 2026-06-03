"""
Esup-Pod - Discipline model.
"""

from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Discipline(models.Model):
    """
    Model representing a specific academic discipline.
    """

    title = models.CharField(_("Title"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, max_length=100, blank=True)
    description = models.TextField(_("Description"), blank=True)
    icon = models.ImageField(
        _("Icon"), upload_to="disciplines/icons/", blank=True, null=True
    )
    sites = models.ManyToManyField(
        Site, related_name="disciplines", blank=True, verbose_name=_("Sites")
    )

    class Meta:
        """Discipline metadata."""

        verbose_name = _("Discipline")
        verbose_name_plural = _("Disciplines")

    def __str__(self):
        """Return the title of the discipline."""
        return self.title

    def save(self, *args, **kwargs):
        """Auto-generate slug on save."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
