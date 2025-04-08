"""Esup-Pod recorder apps."""

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def set_default_site(sender, **kwargs) -> None:
    """Set the default site value if None."""
    from pod.recorder.models import Recorder
    from django.contrib.sites.models import Site

    for rec in Recorder.objects.filter(sites__isnull=True):
        if rec.sites.count() == 0:  # pas forcement utile
            rec.sites.add(Site.objects.get_current())
            rec.save()


def fix_transcript(sender, **kwargs) -> None:
    """
    Transcript field change from boolean to charfield since the version 3.2.0.

    This fix change value to set the default lang value if necessary.
    """
    from pod.recorder.models import Recorder
    from django.db.models import F

    Recorder.objects.filter(transcript="1").update(transcript=F("main_lang"))
    Recorder.objects.filter(transcript="0").update(transcript="")


class RecorderConfig(AppConfig):
    name = "pod.recorder"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Recorders")

    def ready(self) -> None:
        post_migrate.connect(set_default_site, sender=self)
        post_migrate.connect(fix_transcript, sender=self)
