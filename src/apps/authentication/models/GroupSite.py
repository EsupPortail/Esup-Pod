"""
Esup-Pod - GroupSite model and signals for the authentication app.

Links Django Groups to specific Sites.
"""

import logging

from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class GroupSite(models.Model):
    """
    Model linking a Group to one or more Sites.
    Extends the default Group model to allow site-specific group associations.
    """

    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    sites = models.ManyToManyField(Site)

    class Meta:
        """GroupSite model metadata."""

        verbose_name = _("Group site")
        verbose_name_plural = _("Groups site")
        ordering = ["group"]


@receiver(post_save, sender=GroupSite)
def default_site_groupsite(sender, instance, created: bool, **kwargs) -> None:
    """
    Signal receiver to assign the current site to a GroupSite instance if no site is set.
    Triggered after a GroupSite is saved.
    """
    if instance.pk and instance.sites.count() == 0:
        instance.sites.add(Site.objects.get_current())


@receiver(post_save, sender=Group)
def create_groupsite_profile(sender, instance, created: bool, **kwargs) -> None:
    """
    Signal receiver to automatically create a GroupSite profile when a new Group is created.
    """
    if created:
        try:
            GroupSite.objects.get_or_create(group=instance)
        except Exception as e:
            logger.exception(
                "Failed to create GroupSite profile for group %r: %s", instance, e
            )
