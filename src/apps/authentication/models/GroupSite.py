import logging
import traceback

from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

class GroupSite(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    sites = models.ManyToManyField(Site)

    class Meta:
        verbose_name = _("Group site")
        verbose_name_plural = _("Groups site")
        ordering = ["group"]

@receiver(post_save, sender=GroupSite)
def default_site_groupsite(sender, instance, created: bool, **kwargs) -> None:
    if instance.pk and instance.sites.count() == 0:
        instance.sites.add(Site.objects.get_current())


@receiver(post_save, sender=Group)
def create_groupsite_profile(sender, instance, created: bool, **kwargs) -> None:
    if created:
        try:
            GroupSite.objects.get_or_create(group=instance)
        except Exception as e:
            msg = "\n Create groupsite profile ***** Error:%r" % e
            msg += "\n%s" % traceback.format_exc()
            logger.error(msg)
            print(msg)