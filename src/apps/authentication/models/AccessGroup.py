"""
Esup-Pod - AccessGroup model for the authentication app.

This model defines groups of users managed internally or via external auth.
"""

from django.contrib.sites.models import Site
from django.db import models
from django.utils.translation import gettext_lazy as _


class AccessGroup(models.Model):
    """
    Represents a group of users with specific access rights to sites.
    Used to map external authentication groups (LDAP/CAS) to internal permissions.
    """

    display_name = models.CharField(
        max_length=128,
        blank=True,
        default="",
        help_text=_("Readable name of the group."),
    )
    code_name = models.CharField(
        max_length=250,
        unique=True,
        help_text=_("Unique identifier code (e.g., LDAP group name)."),
    )
    sites = models.ManyToManyField(Site, help_text=_("Sites accessible by this group."))
    auto_sync = models.BooleanField(
        _("Auto synchronize"),
        default=False,
        help_text=_(
            "If True, this group is automatically managed via external auth (CAS/LDAP)."
        ),
    )

    class Meta:
        """AccessGroup model metadata."""

        verbose_name = _("Access Group")
        verbose_name_plural = _("Access Groups")
        ordering = ["display_name"]

    def __str__(self) -> str:
        return self.display_name or self.code_name
