"""
Esup-Pod - Contribution role model.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Role(models.Model):
    """Configurable role that can be assigned to a contributor."""

    code = models.SlugField(
        _("Code"),
        max_length=200,
        primary_key=True,
        help_text=_("Stable identifier used by the API and integrations."),
    )
    label = models.CharField(_("Label"), max_length=200)
    is_active = models.BooleanField(_("Active"), default=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        """Meta options for Role."""

        ordering = ["order", "label"]
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")

    def __str__(self):
        return self.label
