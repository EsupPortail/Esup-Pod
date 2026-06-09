"""
Esup-Pod - Cursus model for Metadata.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Cursus(models.Model):
    """Educational levels/cursus categories."""

    name = models.CharField(_("Name"), max_length=100)
    slug = models.SlugField(_("Code"), max_length=10, primary_key=True)
    order = models.PositiveSmallIntegerField(_("Order"), default=0)

    class Meta:
        """Cursus metadata."""

        ordering = ["order", "name"]
        verbose_name = _("Cursus")
        verbose_name_plural = _("Cursus")

    def __str__(self):
        return self.name
