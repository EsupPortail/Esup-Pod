"""
Esup-Pod - Building model.
"""

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from src.apps.live.conf import live_settings


class Building(models.Model):
    """
    Represents a physical or logical location grouping one or more Broadcasters.
    Scoped to one or more Sites for multi-tenancy support.
    """

    name = models.CharField(
        _("Name"),
        max_length=200,
        unique=True,
        help_text=_("Unique name identifying this building or location."),
    )
    headband = models.ImageField(
        _("Headband image"),
        upload_to="live/buildings/",
        blank=True,
        null=True,
        help_text=_("Optional banner image for this building."),
    )
    gmapurl = models.CharField(
        _("Google Maps URL"),
        max_length=250,
        blank=True,
        null=True,
        help_text=_("Optional Google Maps embed URL for this location."),
    )
    sites = models.ManyToManyField(
        Site,
        verbose_name=_("Sites"),
        help_text=_("Sites (portals) where this building is visible."),
    )

    class Meta:
        """Building model metadata."""

        verbose_name = _("Building")
        verbose_name_plural = _("Buildings")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_headband_url(self) -> str:
        """Return the headband URL or fall back to the default thumbnail."""
        if self.headband:
            return self.headband.url
        return "".join([settings.STATIC_URL, live_settings.default_thumbnail])


@receiver(post_save, sender=Building)
def assign_default_site(sender, instance, created: bool, **kwargs) -> None:
    """Automatically assigns the current site to a newly created building."""
    if created and instance.sites.count() == 0:
        instance.sites.add(Site.objects.get_current())
