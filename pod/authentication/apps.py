from django.apps import AppConfig
from django.db.models.signals import post_migrate


def set_default_site(sender, **kwargs):
    from pod.authentication.models import GroupSite
    from pod.authentication.models import Owner
    from django.contrib.sites.models import Site
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
