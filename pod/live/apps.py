from django.apps import AppConfig
from django.db.models.signals import post_migrate


def set_default_site(sender, **kwargs):
    from pod.live.models import Building
    from django.contrib.sites.models import Site
    for build in Building.objects.all():
        if len(build.sites.all()) == 0:
            build.sites.add(Site.objects.get_current())
            build.save()


class LiveConfig(AppConfig):
    name = 'pod.live'

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
