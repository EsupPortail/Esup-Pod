"""
Esup-Pod - Language model for Metadata.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    """Available languages for videos."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Code"), max_length=10, primary_key=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        """Language metadata."""

        ordering = ["order", "name"]
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")

    def __str__(self):
        return self.name
