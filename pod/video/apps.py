from django.apps import AppConfig
from django.db.models.signals import post_migrate


def apply_default_site(obj, site):
    if len(obj.sites.all()) == 0:
        obj.sites.add(site)
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
        apply_default_site(chan, site)
    for dis in Discipline.objects.all():
        apply_default_site(dis, site)
    for typ in Type.objects.all():
        apply_default_site(typ, site)
    for vr in VideoRendition.objects.all():
        apply_default_site(vr, site)


class VideoConfig(AppConfig):
    name = 'pod.video'

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
