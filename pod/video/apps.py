"""Esup-Pod Video App."""
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


def apply_default_site(obj, site):
    if len(obj.sites.all()) == 0:
        obj.sites.add(site)
        obj.save()


def apply_default_site_fk(obj, site):
    if obj.site is None:
        obj.site = site
        obj.save()


def set_default_site(sender, **kwargs):
    from pod.video.models import Video
    from pod.video.models import Channel
    from pod.video.models import Discipline
    from pod.video.models import VideoRendition
    from pod.video.models import Type
    from django.contrib.sites.models import Site

    site = Site.objects.get_current()
    for vid in Video.objects.all():
        apply_default_site(vid, site)
    for chan in Channel.objects.all():
        apply_default_site_fk(chan, site)
    for dis in Discipline.objects.all():
        apply_default_site_fk(chan, site)
    for typ in Type.objects.all():
        apply_default_site(typ, site)
    for vr in VideoRendition.objects.all():
        apply_default_site(vr, site)


def fix_transcript(sender, **kwargs):
    """
    Transcript field change from boolean to charfield since the version 3.2.0
    This fix change value to set the default lang value if necessary
    """
    from pod.video.models import Video
    for vid in Video.objects.all():
        if vid.transcript == '1':
            vid.transcript = vid.main_lang
            vid.save()
        elif vid.transcript == '0':
            vid.transcript = ''
            vid.save()


class VideoConfig(AppConfig):
    name = "pod.video"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Videos")

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
        post_migrate.connect(fix_transcript, sender=self)
