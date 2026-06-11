"""
Esup-Pod - License model for Metadata.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class License(models.Model):
    """Available content licenses for legal protection."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Code"), max_length=20, primary_key=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        """License metadata."""

        ordering = ["order", "name"]
        verbose_name = _("License")
        verbose_name_plural = _("Licenses")

    def __str__(self):
        return self.name
