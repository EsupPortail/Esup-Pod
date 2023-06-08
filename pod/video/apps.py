"""Esup-Pod Video App."""
from django.apps import AppConfig
from django.db.models.signals import post_migrate, pre_migrate
from django.utils.translation import gettext_lazy as _
from django.core import serializers


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
    from pod.video_encode_transcript.models import VideoRendition
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


VIDEO_RENDITION = {}
ENCODING_VIDEO = []
ENCODING_AUDIO = []
ENCODING_LOG = []
ENCODING_STEP = []


class VideoConfig(AppConfig):
    name = "pod.video"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Videos")

    def ready(self):
        post_migrate.connect(set_default_site, sender=self)
        pre_migrate.connect(self.save_previous_data, sender=self)
        post_migrate.connect(self.send_previous_data, sender=self)

    def save_previous_data(self, sender, **kwargs):
        try:
            from pod.video.models import VideoRendition as old_video_rendition
            VIDEO_RENDITION = serializers.serialize("json", old_video_rendition.objects.all())
        except Exception:  # OperationalError or MySQLdb.ProgrammingError
            pass  # print('OperationalError : ', oe)

    def send_previous_data(self, sender, **kwargs):
        for rendition_object in serializers.deserialize("json", VIDEO_RENDITION):
            rendition_object.save()
