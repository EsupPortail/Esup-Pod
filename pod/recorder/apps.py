from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def set_default_site(sender, **kwargs):
    from pod.recorder.models import Recorder
    from django.contrib.sites.models import Site

    for rec in Recorder.objects.all():
        if len(rec.sites.all()) == 0:
            rec.sites.add(Site.objects.get_current())
            rec.save()


class RecorderConfig(AppConfig):
    name = "pod.recorder"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Recorders")

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
