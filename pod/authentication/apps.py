"""Esup-Pod Authentication apps."""

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _


def create_groupsite_if_not_exists(g) -> None:
    from pod.authentication.models import GroupSite

    try:
        GroupSite.objects.get(group=g)
    except ObjectDoesNotExist:
        GroupSite.objects.create(group=g)


def set_default_site(sender, **kwargs) -> None:
    from pod.authentication.models import Owner
    from django.contrib.sites.models import Site
    from django.contrib.auth.models import Group
    from pod.authentication.models import GroupSite

    for g in Group.objects.all():
        create_groupsite_if_not_exists(g)
    for gs in GroupSite.objects.all():
        if gs.sites.count() == 0:
            gs.sites.add(Site.objects.get_current())
            gs.save()
    for owner in Owner.objects.all():
        if owner.sites.count() == 0:
            owner.sites.add(Site.objects.get_current())
            owner.save()


class AuthConfig(AppConfig):
    name = "pod.authentication"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Authentication")

    def ready(self) -> None:
        post_migrate.connect(set_default_site, sender=self)
