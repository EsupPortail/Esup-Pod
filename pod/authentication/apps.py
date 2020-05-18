from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.core.exceptions import ObjectDoesNotExist


def create_groupsite_if_not_exists(g):
    from pod.authentication.models import GroupSite
    try:
        GroupSite.objects.get(group=g)
    except ObjectDoesNotExist:
        GroupSite.objects.create(group=g)


def set_default_site(sender, **kwargs):
    from pod.authentication.models import Owner
    from django.contrib.sites.models import Site
    from django.contrib.auth.models import Group
    from pod.authentication.models import GroupSite
    for g in Group.objects.all():
        create_groupsite_if_not_exists(g)
    for gs in GroupSite.objects.all():
        if len(gs.sites.all()) == 0:
            gs.sites.add(Site.objects.get_current())
            gs.save()
    for owner in Owner.objects.all():
        if len(owner.sites.all()) == 0:
            owner.sites.add(Site.objects.get_current())
            owner.save()


class AuthConfig(AppConfig):
    name = 'pod.authentication'

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
